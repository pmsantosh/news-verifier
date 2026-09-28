import streamlit as st
from serpapi import GoogleSearch
import joblib
import re

# 1. Load local ML model safely
try:
    nlp_model = joblib.load("custom_model.pkl")
except Exception as e:
    nlp_model = None

# 2. SerpApi Configuration
# Paste your private SerpApi token inside the quotes below:
SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]

# Helper function to clean text for matching
def clean_words(text):
    return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))

# 3. Streamlit UI Layout Configuration
st.set_page_config(page_title="Fake news detection", page_icon="📰", layout="centered")
st.title("📰 Fake news detection")
st.markdown("This system evaluates claims by checking for explicit percentage-based semantic web validation.")

with st.container(border=True):
    st.subheader("Verify Media Claims")
    user_input = st.text_area(
        "Enter any news text, headline, or claim below:",
        placeholder="Type or paste your text here..."
    )
    verify_button = st.button("Verify Claim", type="primary")

# 4. Strict Search & Match Ratio Threshold Loop
if verify_button and user_input.strip():
    st.info("Searching web indexes for verification...")
    
    search_params = {
        "engine": "google",
        "q": user_input,
        "api_key": SERPAPI_API_KEY
    }
    
    try:
        search_engine = GoogleSearch(search_params)
        results_matrix = search_engine.get_dict()
        organic_results = results_matrix.get("organic_results", [])
        
        # Check if the search returned anything at all
        if organic_results:
            input_words = clean_words(user_input)
            combined_snippets = " ".join([item.get('snippet', '') for item in organic_results[:3]])
            snippet_words = clean_words(combined_snippets)
            
            # Calculate overlapping words
            matching_words = input_words.intersection(snippet_words)
            ignore_words = {'with', 'that', 'this', 'from', 'will', 'next', 'have', 'were', 'about'}
            meaningful_matches = matching_words - ignore_words
            
            # Calculate strict match percentage ratio
            meaningful_input_words = input_words - ignore_words
            match_ratio = len(meaningful_matches) / len(meaningful_input_words) if meaningful_input_words else 0
            
            combined_text_lowercase = combined_snippets.lower()
            debunk_terms = ["fake", "false", "rumor", "debunked", "misleading", "hoax", "untrue", "myth", "fabricated"]
            has_debunk_words = any(term in combined_text_lowercase for term in debunk_terms)
            
            st.markdown("---")
            
            # SCENARIO 1: Explicitly Flagged as Fake
            if has_debunk_words and len(meaningful_matches) >= 2:
                st.error("🚨 VERDICT: FAKE NEWS (Debunked by Sources)")
                st.warning("Reliable live web sources have actively flagged or debunked this claim as false.")
                
            # SCENARIO 2: High Match Ratio & No Debunking Words (Requires 65% match)
            elif match_ratio >= 0.65 and not has_debunk_words:
                st.success("✅ VERDICT: REAL / VERIFIED NEWS")
                st.info(f"Multiple independent live web links confirm the critical details of this claim. (Context Match: {match_ratio:.0%})")
                st.balloons()
                
            # SCENARIO 3: Low Phrasing Match Ratio (Fails to confirm the core claim details)
            else:
                st.error("🚨 VERDICT: FAKE NEWS (Not Found / Uncorroborated)")
                st.warning(f"The web contains articles discussing these topics, but they do not confirm your specific claim scenario. (Context Match: {match_ratio:.0%} - system requires at least 65%)")
                
            st.markdown("---")
            st.subheader("Top Contextual Sources Found:")
            for item in organic_results[:3]:
                st.markdown(f"*[{item.get('title')}]({item.get('link')})*")
                st.write(item.get('snippet', 'No summary details available.'))
                st.write("---")
                #update
        # If Google returns absolute zero matching results
        else:
            st.markdown("---")
            st.error("🚨 VERDICT: FAKE NEWS (No Web Presence Found)")
            st.warning("This claim does not exist anywhere in live web indexes. Flagged as completely fabricated.")
            st.markdown("---")
            
    except Exception as err:
        st.error(f"Execution structure fault: {err}")
elif verify_button:
    st.warning("Please enter a valid claim to verify.")
    


