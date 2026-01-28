import streamlit as st

def show_editor(pid, title, content, img, cat, desc, tags, cursor, conn):
    """Article Editor with SEO, Meta, and Category fields"""
    with st.expander(f"📦 [{cat}] - {title}", expanded=False):
        # SEO & Image Section
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if img and img != "Not Generated":
                st.image(img, width="stretch", caption="AI Featured Image") #
            
            st.subheader("🛠️ SEO & Meta")
            f_cat = st.selectbox("Category", ["Technology", "Business", "Sports", "India", "General"], 
                                 index=0, key=f"cat_{pid}")
            f_desc = st.text_area("Meta Description", value=str(desc), key=f"desc_{pid}")
            f_tags = st.text_input("SEO Tags", value=str(tags), key=f"tags_{pid}")
            
        with col2:
            st.subheader("🖋️ Content Editor")
            f_title = st.text_input("Headline", value=title, key=f"tit_{pid}")
            f_content = st.text_area("Body (300-400 words)", value=content, height=400, key=f"con_{pid}")
            
            # Action Buttons
            b1, b2 = st.columns(2)
            if b1.button("🚀 Publish", key=f"pub_{pid}", type="primary"):
                # WordPress publishing logic calls here
                cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                conn.commit()
                st.success("Article Published!")
                st.rerun()
            
            if b2.button("❌ Reject", key=f"rej_{pid}"):
                cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                conn.commit()
                st.rerun()
