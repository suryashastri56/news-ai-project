import streamlit as st

def show_editor(pid, title, content, img, cat, desc, tags, cursor, conn):
    """
    Article Editor module with fixed SEO, Meta, and Image UI
    """
    # Expander for clean UI
    with st.expander(f"📦 [{cat}] - {title}", expanded=False):
        
        # 1. Main Layout: Image & SEO on left, Content on right
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            # AI Featured Image Display
            if img and img != "Not Generated":
                # width="stretch" used to fix deprecation warning
                st.image(img, width="stretch", caption="📸 AI Featured Image")
            else:
                st.warning("🖼️ Image not generated for this article.")
            
            st.divider()
            
            # SEO & Meta Configuration
            st.subheader("🛠️ SEO & Meta Details")
            
            # Category Dropdown
            cats = ["Technology", "Business", "Sports", "India", "General", "Health", "Entertainment"]
            try:
                current_cat_idx = cats.index(cat) if cat in cats else 0
            except: current_cat_idx = 0
            
            f_cat = st.selectbox("Category", cats, index=current_cat_idx, key=f"cat_{pid}")
            
            # Meta Description & Tags
            f_desc = st.text_area("Meta Description (Excerpt)", value=str(desc), height=100, key=f"desc_{pid}")
            f_tags = st.text_input("SEO Tags (Keywords)", value=str(tags), key=f"tags_{pid}")
            
        with col2:
            # Content Editor Section
            st.subheader("🖋️ Content Editor")
            f_title = st.text_input("Headline Editor", value=title, key=f"tit_{pid}")
            
            # Article Body (300-400 words)
            f_content = st.text_area("Article Body", value=content, height=450, key=f"con_{pid}")
            
            # Word Count Indicator
            word_count = len(f_content.split())
            st.caption(f"Word Count: {word_count} words (Target: 300-400)")

            st.divider()
            
            # --- ACTION BUTTONS ---
            btn_col1, btn_col2 = st.columns(2)
            
            if btn_col1.button("🚀 Publish to WordPress", key=f"pub_{pid}", type="primary", width="stretch"):
                # Database update before publishing
                cursor.execute("""
                    UPDATE news_articles 
                    SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, status='published' 
                    WHERE id=?
                """, (f_title, f_content, f_cat, f_desc, f_tags, pid))
                conn.commit()
                st.success("Article status updated to 'Published'!")
                st.rerun() # Refresh to move article to Published Tab

            if btn_col2.button("🗑️ Reject Article", key=f"rej_{pid}", width="stretch"):
                cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                conn.commit()
                st.info("Article moved to Rejected tab.")
                st.rerun()
