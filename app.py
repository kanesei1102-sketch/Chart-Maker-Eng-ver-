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
st.set_page_config(page_title="Sci-Graph Maker Pro", layout="wide")
st.title("📊 Sci-Graph Maker Pro (Multi-Type Edition)")
st.markdown("""
**Description:** Generate publication-ready figures with high scientific integrity.  
**Features:** Switch between Bar (Mean), Box (Median), and Violin (Distribution) plots with a single click.
""")

# Session State for dynamic conditions
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.header("Data Settings")
    st.button("＋ Add Condition", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ Remove Condition", on_click=remove_condition)
    
    st.divider()
    st.subheader("Group Labels")
    group1_name = st.text_input("Group 1 Name", value="Control")
    group2_name = st.text_input("Group 2 Name", value="Target")
    
    st.divider()
    st.header("Graph Configuration")
    
    # Switch between graph types (Default: Bar Plot)
    graph_type = st.selectbox("Select Graph Type", 
                              ["Bar Plot (Mean ± SD)", 
                               "Box Plot (Median + IQR)", 
                               "Violin Plot (Distribution)"])
    
    y_axis_label = st.text_input("Y-axis Title", value="Relative Intensity (%)")
    
    st.divider()
    st.header("Design & Style")
    
    with st.expander("🎨 Colors & Legend", expanded=True):
        color1 = st.color_picker("Group 1 Color", "#999999") 
        color2 = st.color_picker("Group 2 Color", "#66c2a5") 
        show_legend = st.checkbox("Show Legend", value=True)

    with st.expander("📏 Layout Adjustment", expanded=True):
        width = st.slider("Element Width", 0.2, 1.0, 0.6, 0.1)
        gap = st.slider("Group Gap", 0.0, 0.5, 0.05, 0.01)
        if "Bar" in graph_type:
            cap_size = st.slider("Error Bar Capsize", 0.0, 10.0, 5.0, 0.5)

    with st.expander("✨ Individual Points (Strip Plot)", expanded=True):
        show_points = st.checkbox("Show Data Points", value=True)
        st.caption("For large datasets (N > 1000), reduce size and increase alpha.")
        dot_size = st.slider("Dot Size", 1, 100, 20) 
        dot_alpha = st.slider("Dot Alpha (Transparency)", 0.1, 1.0, 0.6, 0.1)
        jitter_strength = st.slider("Jitter Strength", 0.0, 0.3, 0.04, 0.01)

# ---------------------------------------------------------
# Data Input Section
# ---------------------------------------------------------
cond_data_list = [] 

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        def_name = ["Day 0", "Day 3", "Day 7", "Day 14"][i] if i < 4 else f"Cond_{i+1}"
        
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### Condition {i+1}")
            cond_name = st.text_input("Condition Name", value=def_name, key=f"name_{i}")
            sig_label = st.text_input("Significance Label", placeholder="e.g. **", key=f"sig_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            # Demo values
            def_val1 = "100\n105\n98\n102" if i == 0 else ""
            input1 = st.text_area(f"Data 1", value=def_val1, height=100, key=f"d1_{i}", label_visibility="collapsed")

        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_val2 = "140\n135\n150\n145" if i == 0 else ""
            input2 = st.text_area(f"Data 2", value=def_val2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        vals1, vals2 = [], []
        if input1:
            try: vals1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
            except: pass
        if input2:
            try: vals2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
            except: pass
        
        if vals1 or vals2:
            cond_data_list.append({'name': cond_name, 'g1': vals1, 'g2': vals2, 'sig': sig_label})

# ---------------------------------------------------------
# Plotting Logic
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("Preview")
    
    try:
        all_vals = []
        for item in cond_data_list:
            all_vals.extend(item['g1'])
            all_vals.extend(item['g2'])
        
        if not all_vals:
            st.warning("No valid numeric data entered.")
            st.stop()
            
        global_max = max(all_vals)
        y_limit = global_max * 1.35
        
        n_plots = len(cond_data_list)
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3, 5), sharey=True)
        if n_plots == 1: axes = [axes]
            
        plt.subplots_adjust(wspace=0)
        plt.rcParams['font.family'] = 'sans-serif'

        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            has_g1, has_g2 = len(g1) > 0, len(g2) > 0
            
            if has_g1 and has_g2:
                pos1, pos2 = -(width/2 + gap/2), +(width/2 + gap/2)
            else:
                pos1, pos2 = 0, 0

            # Sub-function for group plotting
            def plot_group(ax, pos, vals, color):
                if len(vals) == 0: return
                
                # A. Bar Plot (Original logic)
                if "Bar" in graph_type:
                    mean = np.mean(vals)
                    std = np.std(vals, ddof=1) if len(vals) > 1 else 0
                    ax.bar(pos, mean, width=width, color=color, edgecolor='black', zorder=1, alpha=0.9)
                    ax.errorbar(pos, mean, yerr=std, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                
                # B. Box Plot
                elif "Box" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=width, patch_artist=True, 
                               showfliers=False,
                               medianprops=dict(color="black", linewidth=1.5),
                               boxprops=dict(facecolor=color, color="black"),
                               whiskerprops=dict(color="black"),
                               capprops=dict(color="black"), zorder=1)
                
                # C. Violin Plot
                elif "Violin" in graph_type:
                    parts = ax.violinplot(vals, positions=[pos], widths=width, showmeans=False, showextrema=False)
                    for pc in parts['bodies']:
                        pc.set_facecolor(color)
                        pc.set_edgecolor('black')
                        pc.set_alpha(0.8)
                        pc.set_zorder(1)

                # Individual Points (Strip Plot) - Overlay for all types
                if show_points:
                    noise = np.random.normal(0, jitter_strength * width, len(vals))
                    edge_c = 'gray' if dot_size > 10 else 'none'
                    ax.scatter(pos + noise, vals, color='white', edgecolor=edge_c, 
                               s=dot_size, alpha=dot_alpha, zorder=3)

            plot_group(ax, pos1, g1, color1)
            plot_group(ax, pos2, g2, color2)

            # X-axis setup
            ticks, labels = [], []
            if has_g1: ticks.append(pos1); labels.append(group1_name)
            if has_g2: ticks.append(pos2); labels.append(group2_name)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=11)
            ax.set_title(data['name'], fontsize=12, pad=10)
            
            # Significance indicators
            sig_text = data['sig']
            if sig_text:
                current_max = 0
                if has_g1: current_max = max(current_max, np.max(g1))
                if has_g2: current_max = max(current_max, np.max(g2))
                y_line = current_max * 1.15
                h = current_max * 0.03
                lx_start, lx_end = (pos1, pos2) if has_g1 and has_g2 else (pos1-0.1, pos1+0.1)
                ax.plot([lx_start, lx_start, lx_end, lx_end], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                ax.text((lx_start+lx_end)/2, y_line + current_max*0.02, sig_text, ha='center', va='bottom', fontsize=14, color='k')

            # Spines and Decoration
            ax.set_ylim(0, y_limit)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            if i == 0:
                ax.set_ylabel(y_axis_label, fontsize=14)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False, labelleft=False)

        # Legend
        if show_legend:
            handles = [mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name),
                       mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name)]
            fig.legend(handles=handles, loc='center left', bbox_to_anchor=(0.92, 0.5), frameon=False, fontsize=12)

        st.pyplot(fig)

        # Download with JST Timestamp
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=300) 
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("Download Image", data=img, 
                           file_name=f"graph_{now.strftime('%Y%m%d_%H%M%S')}.png", 
                           mime="image/png")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please enter data to generate the preview.")
