"""Journal tab — V3-202 Research Journal Integration."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.research_journal_experience import render_research_journal_experience
from ui.theme import APEX_PARTNER_EXPERIENCE_CSS


def render_research_journal() -> None:
    st.markdown(APEX_PARTNER_EXPERIENCE_CSS, unsafe_allow_html=True)
    render_research_journal_experience()
