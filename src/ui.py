import os
import sys
from pathlib import Path
import requests
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Kestrel Service Routing Console",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished interface
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        margin-top: 15px;
    }
    .team-badge {
        display: inline-block;
        font-size: 1.5rem;
        font-weight: 700;
        color: #1D4ED8;
        background-color: #DBEAFE;
        padding: 6px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .alert-review {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 4px;
        color: #92400E;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🦅 Kestrel Home — Service Routing Console</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Queue Assignment & Explainable Decision Support (Operations Policy v4.1 Compliant)</div>', unsafe_allow_html=True)

# Sidebar: System Status & Presets
with st.sidebar:
    st.header("⚙️ Service Configuration")
    api_endpoint = st.text_input("FastAPI Endpoint", value=API_URL)
    
    st.subheader("System Health")
    try:
        health_resp = requests.get(f"{api_endpoint}/health", timeout=2)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            st.success(f"API Online | Model Ready ({health_data['version']})")
        else:
            st.warning("API responding with non-200 code.")
    except Exception:
        st.error("API Offline. Please start FastAPI service:\n`uvicorn src.api:app --port 8000`")

    st.markdown("---")
    st.subheader("📋 Example Presets")
    preset_choice = st.selectbox(
        "Load realistic test request:",
        [
            "Custom Input",
            "1. Water Purifier Breakdown (Repairs)",
            "2. Payment for Installation (Policy §3 Edge Case)",
            "3. Genuine Billing / GST Invoice",
            "4. Spares / Filter Kit (Filters & Consumables)",
            "5. Ambiguous Purifier Query",
            "6. Out-of-Warranty Repair Inquiry"
        ]
    )

# Preset definitions
preset_data = {
    "1. Water Purifier Breakdown (Repairs)": {
        "channel": "chat",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
        "request_text": "water purifier leaking water from bottom, display showing error E02 kindly send technician"
    },
    "2. Payment for Installation (Policy §3 Edge Case)": {
        "channel": "ivr",
        "product_family": "Ceiling Fan",
        "warranty_status": "in_warranty",
        "request_text": "i paid online for installation but installer did not turn up for ceiling fan kindly resolve"
    },
    "3. Genuine Billing / GST Invoice": {
        "channel": "email",
        "product_family": "Room Heater",
        "warranty_status": "out_of_warranty",
        "request_text": "good morning, invoice not received for room heater order KO2604819, please send updated GST invoice copy"
    },
    "4. Spares / Filter Kit (Filters & Consumables)": {
        "channel": "whatsapp",
        "product_family": "Water Purifier",
        "warranty_status": "shield",
        "request_text": "sir want AMC filter kit and spare sediment candle for purifier thanks"
    },
    "5. Ambiguous Purifier Query": {
        "channel": "chat",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
        "request_text": "please call me about my purifier very disappointed"
    },
    "6. Out-of-Warranty Repair Inquiry": {
        "channel": "ivr",
        "product_family": "Air Fryer",
        "warranty_status": "out_of_warranty",
        "request_text": "air fryer motor making strange humming sound and not heating up, how much will repair cost?"
    }
}

current_vals = preset_data.get(preset_choice, {
    "channel": "chat",
    "product_family": "Water Purifier",
    "warranty_status": "in_warranty",
    "request_text": ""
})

# Intake Form
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Request Intake Details")
    with st.form("routing_form"):
        req_id = st.text_input("Request ID (Optional)", value="SR510823")
        
        channel_opts = ["chat", "whatsapp", "ivr", "email"]
        channel = st.selectbox(
            "Intake Channel",
            channel_opts,
            index=channel_opts.index(current_vals["channel"])
        )
        
        prod_opts = [
            "Water Purifier", "Air Fryer", "Mixer Grinder",
            "Induction Cooktop", "Room Heater", "Ceiling Fan", "Robot Vacuum"
        ]
        product_family = st.selectbox(
            "Product Family",
            prod_opts,
            index=prod_opts.index(current_vals["product_family"])
        )
        
        warr_opts = ["in_warranty", "out_of_warranty", "shield"]
        warranty_status = st.selectbox(
            "Warranty Status",
            warr_opts,
            index=warr_opts.index(current_vals["warranty_status"])
        )
        
        request_text = st.text_area(
            "Customer Message / IVR Transcript",
            value=current_vals["request_text"],
            height=120,
            placeholder="Type customer's opening message..."
        )
        
        submit_btn = st.form_submit_button("🚀 Route Request")

with col2:
    st.subheader("🎯 Routing & Explanation Output")
    if submit_btn:
        if not request_text.strip():
            st.error("Please enter request text to classify.")
        else:
            payload = {
                "request_id": req_id.strip() if req_id.strip() else None,
                "channel": channel,
                "product_family": product_family,
                "warranty_status": warranty_status,
                "request_text": request_text.strip(),
                "source": "crm"
            }
            
            with st.spinner("Classifying request via local FastAPI service..."):
                try:
                    resp = requests.post(f"{api_endpoint}/predict", json=payload, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown("#### Assigned Destination Queue:")
                        st.markdown(f'<div class="team-badge">{data["predicted_team"]}</div>', unsafe_allow_html=True)
                        
                        # Confidence
                        conf = data["confidence"]
                        st.write(f"**Calibrated Confidence:** {conf*100:.1f}%")
                        st.progress(conf)
                        
                        # Human review alert
                        if data.get("review_recommended"):
                            st.markdown(
                                '<div class="alert-review">⚠️ Operational Human Review Recommended: Elevated transfer risk or policy boundary detected.</div>',
                                unsafe_allow_html=True
                            )
                        
                        # Runner up
                        if data.get("runner_up_team"):
                            st.caption(f"Runner-up queue: **{data['runner_up_team']}** ({data['runner_up_confidence']*100:.1f}%)")
                        
                        # Evidence Reasons
                        st.markdown("#### 💡 Decision Evidence & Policy Considerations:")
                        for reason in data["reasons"]:
                            st.info(f"• {reason}")
                            
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"API Error ({resp.status_code}): {resp.text}")
                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to FastAPI service at {api_endpoint}. Please ensure the server is running.")
                except Exception as ex:
                    st.error(f"Unexpected error: {str(ex)}")
    else:
        st.info("Fill in the ticket details on the left or select a preset, then click **Route Request**.")
