import streamlit as st

# -------------------------------------------------
# PEET UNIVERSAL HERO THEME
# -------------------------------------------------

def inject_peet_theme():
    st.markdown(
        """
        <style>
        .peet-hero {
            position: relative;
            width: 100%;
            height: 420px;
            border-radius: 18px;
            overflow: hidden;
            margin-bottom: 2.5rem;
            background-size: cover;
            background-position: center;
        }

        .peet-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(
                to bottom,
                rgba(0,0,0,0.25) 0%,
                rgba(0,0,0,0.55) 60%,
                rgba(0,0,0,0.75) 100%
            );
        }

        .peet-content {
            position: absolute;
            bottom: 40px;
            left: 40px;
            color: white;
            max-width: 720px;
        }

        .peet-content h1 {
            font-size: 2.6rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .peet-content p {
            font-size: 1.05rem;
            opacity: 0.9;
        }

        .peet-meta {
            margin-top: 0.8rem;
            font-size: 0.95rem;
            opacity: 0.9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_peet_hero(title, subtitle, image_url, kcal=None, protein=None, fat=None, carbs=None):
    inject_peet_theme()

    meta = ""
    if kcal:
        meta = f"{kcal} kcal"
        if protein:
            meta += f" · E {protein} g"
        if fat:
            meta += f" · V {fat} g"
        if carbs:
            meta += f" · KH {carbs} g"

    st.markdown(
        f"""
        <div class="peet-hero" style="background-image: url('{image_url}');">
            <div class="peet-overlay"></div>
            <div class="peet-content">
                <h1>{title}</h1>
                <p>{subtitle}</p>
                <div class="peet-meta">{meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
