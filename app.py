import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro Max", layout="wide")
st.title("📊 Sci-Graph Maker: Professional Workflow")
st.markdown("""
**Hybrid Architecture:** Seamlessly integrate data from the Image Quantifier CSV while adding manual control groups as needed.  
**Scientific Standards:** High-precision visualization supporting Bar, Box, and Violin plots with SD/SEM options.
""")

# Session State Management
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 0 

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 0:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. Global Configuration")
    graph_type = st.selectbox("Plot Type", ["Bar Plot (Mean)", "Box Plot (Median)", "Violin Plot (Density)"])
    
    if "Bar" in graph_type:
        error_bar_type = st.radio("Error Bar Type:", ["SD (Standard Deviation)", "SEM (Standard Error)"])
    
    fig_title = st.text_input("Figure Title", value="Experimental Analysis")
    y_axis_label = st.text_input("Y-axis Label", value="Quantified Value")
    manual_y_max = st.number_input("Fixed Y-axis Max (0 for Auto)", value=0.0)

    st.divider()
    st.header("2. Aesthetics & Legend")
    
    with st.expander("🎨 Group Labels & Colors", expanded=True):
        group1_name = st.text_input("Group 1 Label", value="Control")
        color1 = st.color_picker("Group 1 Color", "#999999") 
        
        st.divider()
        
        group2_name = st.text_input("Group 2 Label", value="Target")
        color2 = st.color_picker("Group 2 Color", "#66c2a5") 
        
        st.divider()
        show_legend = st.checkbox("Show Legend", value=True)

    with st.expander("✨ Strip Plot Adjustment"):
        show_points = st.checkbox("Show Individual Points (N)", value=True)
        dot_size = st.slider("Dot Size", 1, 100, 20) 
        dot_alpha = st.slider("Alpha (Transparency)", 0.1, 1.0, 0.6)
        jitter_strength = st.slider("Jitter Strength", 0.0, 0.3, 0.04)

# ---------------------------------------------------------
# Main: Data Input Section
# ---------------------------------------------------------
cond_data_list = [] 

# --- A. CSV Integration ---
st.header("📂 Step 1: Import Analyzed Data")
uploaded_csv = st.file_uploader("Upload CSV from Image Quantifier (Optional)", type="csv")

if uploaded_csv:
    ext_df = pd.read_csv(uploaded_csv)
    for g_name in ext_df['Group'].unique():
        g_data = ext_df[ext_df['Group'] == g_name]['Value'].tolist()
        cond_data_list.append({
            'name': g_name,
            'g1': g_data, 
            'g2': [], 
            'sig': "",
            'source': 'csv'
        })
    st.success(f"Successfully imported {len(ext_df['Group'].unique())} groups from CSV.")

st.divider()

# --- B. Manual Addition ---
st.header("✍️ Step 2: Add Manual Conditions")
col_btn1, col_btn2, _ = st.columns([1, 1, 3])
with col_btn1:
    st.button("＋ Add Condition", on_click=add_condition)
with col_btn2:
    st.button("－ Remove Condition", on_click=remove_condition)

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown(f"**Manual Condition {i+1}**")
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        with c_meta:
            cond_name = st.text_input("Cond. Name", value=f"Exp_{i+1}", key=f"name_{i}")
            sig_label = st.text_input("Significance", placeholder="e.g. **", key=f"sig_{i}")
        with c_g1:
            input1 = st.text_area(f"{group1_name} Data", key=f"d1_{i}", help="Line separated values")
        with c_g2:
            input2 = st.text_area(f"{group2_name} Data", key=f"d2_{i}", help="Optional: Comparison group")

        vals1, vals2 = [], []
        try:
            if input1: vals1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
            if input2: vals2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
        except:
            st.error(f"Invalid numeric input in Condition {i+1}.")
            
        if vals1 or vals2:
            cond_data_list.append({
                'name': cond_name, 
                'g1': vals1, 
                'g2': vals2, 
                'sig': sig_label,
                'source': 'manual'
            })

# ---------------------------------------------------------
# Visualization Section
# ---------------------------------------------------------
if cond_data_list:
    st.divider()
    st.subheader("📊 Final Result Preview")
    try:
        n_plots = len(cond_data_list)
        fig, axes = plt.subplots(1, n_plots, figsize=(max(n_plots * 3.5, 6), 5), sharey=True)
        if n_plots == 1: axes = [axes]
        
        plt.subplots_adjust(wspace=0.1)
        fig.suptitle(fig_title, fontsize=16, y=1.08)

        all_vals = []
        for d in cond_data_list: all_vals.extend(d['g1'] + d['g2'])
        y_limit = manual_y_max if manual_y_max > 0 else max(all_vals) * 1.35

        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            
            w, gap_val = 0.6, 0.05
            pos1, pos2 = (-(w/2 + gap_val/2), +(w/2 + gap_val/2)) if len(g1)>0 and len(g2)>0 else (0, 0)

            def draw_element(ax, pos, vals, color):
                if len(vals) == 0: return
                if "Bar" in graph_type:
                    mean = np.mean(vals)
                    err = np.std(vals, ddof=1)
                    if error_bar_type == "SEM (Standard Error)":
                        err = err / np.sqrt(len(vals))
                    ax.bar(pos, mean, width=w, color=color, edgecolor='black', zorder=1)
                    ax.errorbar(pos, mean, yerr=err, fmt='none', color='black', capsize=5, zorder=2)
                elif "Box" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=w, patch_artist=True, showfliers=False,
                               boxprops=dict(facecolor=color), medianprops=dict(color="black"), zorder=1)
                elif "Violin" in graph_type:
                    vp = ax.violinplot(vals, positions=[pos], widths=w, showextrema=False)
                    for pc in vp['bodies']: pc.set_facecolor(color); pc.set_alpha(0.7); pc.set_zorder(1)

                if show_points:
                    noise = np.random.normal(0, jitter_strength * w, len(vals))
                    ax.scatter(pos + noise, vals, color='white', edgecolor='gray', s=dot_size, alpha=dot_alpha, zorder=3)

            draw_element(ax, pos1, g1, color1)
            draw_element(ax, pos2, g2, color2)

            if len(g1)>0 and len(g2)>0:
                ax.set_xticks([pos1, pos2])
                ax.set_xticklabels([group1_name, group2_name], fontsize=9)
            else:
                ax.set_xticks([0])
                ax.set_xticklabels([""], fontsize=9)
            
            ax.set_title(data['name'], fontsize=11, pad=10)
            ax.set_ylim(0, y_limit)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            if i == 0: ax.set_ylabel(y_axis_label, fontsize=12)
            else: ax.spines['left'].set_visible(False); ax.tick_params(axis='y', left=False)

        if show_legend:
            handles = [mpatches.Patch(facecolor=color1, label=group1_name), 
                       mpatches.Patch(facecolor=color2, label=group2_name)]
            fig.legend(handles=handles, loc='center left', bbox_to_anchor=(0.98, 0.5), frameon=False)

        st.pyplot(fig)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        # JST Timestamp for the filename
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("📥 Download Figure", buf, f"publication_graph_{now.strftime('%Y%m%d_%H%M%S')}.png")

    except Exception as e:
        st.error(f"Plotting Error: {e}")
else:
    st.info("Awaiting input: Upload a CSV or add a manual condition.")
