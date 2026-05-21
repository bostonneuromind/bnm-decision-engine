// ============================================================
// Decision Catcher - Common JavaScript
// Boston Neuromind LLC · CNA v7
// ============================================================

const CONFIG = {
  apiBase: '/api',
  passwordKey: 'decisionOK',
  password: 'bnm1#',
  langKey: 'decisionLang',
  defaultLang: 'ko',
};

// ============================================================
// 언어 토글 (i18n) - 전체 사이트 통합
// ============================================================

const I18N = {
  ko: {
    // 공통 메뉴
    home: 'Home',
    new_client: '새 클라이언트',
    outcome: '4주 Outcome',
    manual: '매뉴얼',
    beta_guide: '베타 가이드',
    admin: '← Admin',
    logout: 'Logout',
    lang_toggle: 'EN',
    clinician_manual: '임상가 매뉴얼',

    // 공통 버튼
    btn_start: '시작',
    btn_next: '다음',
    btn_back: '이전',
    btn_save: '저장',
    btn_submit: '제출',
    btn_cancel: '취소',
    btn_close: '닫기',
    btn_confirm: '확인',
    btn_continue: '계속',
    btn_reset: '초기화',
    btn_download: '다운로드',
    btn_print: '인쇄',

    // index.html - 히어로
    badge_v7: 'CNA v7.0 · Round 7-10 통합',
    site_title: 'Decision Catcher',
    site_subtitle: '감별 진단 + 공존 진단 + 적응적 훈련',
    site_company: 'Boston Neuromind LLC · Catcher Navigator Algorithm',
    btn_start_assessment: '새 클라이언트 평가 시작',
    btn_view_manual: '매뉴얼 자료',

    // index.html - 왜 이 시스템인가
    why_title: '왜 이 시스템인가',
    why_p1_intro: '기존 5축 매핑 시스템 (CNA v6)에',
    why_p1_highlight: '감별 진단 + 공존 진단 자료',
    why_p1_outro: '를 추가했습니다. 한 클라이언트의 임상 점수 안에서 ADHD, GAD, MDD가 각각 얼마나 기여하는지 분해하고, 그에 맞는 훈련 카드를 적응적으로 제공합니다.',
    why_principle_label: '핵심 원리:',
    why_principle_text: '같은 "주의력 0.39" 점수도, ADHD가 primary인 경우와 GAD가 primary인 경우의 치료 전략이 완전히 다릅니다. 미인지 ADHD에 SSRI 단독 처방은 효과 없음 (McIntosh et al. 2009). 진단 정확도가 치료 효과의 기반입니다.',

    // index.html - v7 모듈
    v7_modules_title: 'v7 추가 모듈 (Round 7-10)',
    module1_title: '① Differential Diagnosis Engine',
    module1_desc: '증상 호소 + 인지 5축 + 바이오마커 + 시간 정보 → Bayesian 감별 진단',
    module1_small: 'DSM-5-TR canonical pattern matching',
    module2_title: '② Comorbidity Decomposition',
    module2_desc: '임상 점수를 진단 source별로 분해 (예: Attention 0.39 = ADHD 0.25 + GAD 0.10 + MDD 0.04)',
    module3_title: '③ Cognitive Simulator',
    module3_desc: '"이 인지축을 박으면 임상축이 어떻게 변할까?" Counterfactual 시뮬레이션',
    module4_title: '④ Adaptive Re-routing',
    module4_desc: '4주 outcome → 예상 반응 패턴 비교 → 불일치 시 진단 자동 재구성',

    // index.html - 5축
    axis_title: '5축 임상 영역',
    axis_attention: '주의력',
    axis_attention_desc: 'CPT, ASRS',
    axis_learning: '학습 효율',
    axis_learning_desc: 'N-back, retention',
    axis_peak: '수행 최적화',
    axis_peak_desc: '시간 추정, HRV',
    axis_anxiety: '불안 관리',
    axis_anxiety_desc: 'HRV, GAD-7',
    axis_depression: '기분 안정',
    axis_depression_desc: 'PHQ-9, BA count',

    // index.html - 임상 근거
    evidence_title: '임상 근거',
    evidence_col1: '매핑 / 알고리즘',
    evidence_col2: '임상 근거',
    evidence_wm: 'Working Memory → Learning (r=0.43)',
    evidence_wm_src: 'Meta-analysis, n=7947',
    evidence_ei: 'Emotional Intelligence → Academic (r=0.39)',
    evidence_ei_src: 'EI-AP meta-analysis 2023',
    evidence_er: 'Emotion Regulation 효과 (d=0.605)',
    evidence_er_src: 'Aldao et al. 2010',
    evidence_ai: 'Active Inference 임상 적용',
    evidence_ai_src: 'Friston 2010-2025',
    evidence_adhd: '성인 ADHD 공존률 50-80%',
    evidence_adhd_src: 'Frontiers 2025',
    evidence_temporal: '감별의 핵심 = temporal pattern',
    evidence_temporal_src: 'Multiple',
    evidence_ssri: '미인지 ADHD에 SSRI 단독 = 실패',
    evidence_ssri_src: 'McIntosh et al. 2009',

    // index.html - 다음 단계
    next_steps_title: '다음 단계',
    step1_title: '새 클라이언트 평가',
    step1_desc: 'Entry Protocol 5 + 증상 + 시간 정보 + 클라이언트 목표',
    step2_title: '임상 리포트 검토',
    step2_desc: '5축 점수 + DDE + Decomposition + Simulator',
    step3_title: '훈련 프로토콜 운영',
    step3_desc: '4-8주, 시스템 추천 + 임상가 override',
    step4_title: '4주 outcome 입력',
    step4_desc: 'Adaptive Re-routing 자동 실행',
    btn_get_started: '시작하기',

    // Footer
    footer_company: 'Boston Neuromind LLC · CNA v7.0.0 · 2026',
    footer_author: 'Alex Kwon (BCN, PhD)',

    // clinician.html
    clinician_title: '새 클라이언트 평가',
    clinician_subtitle: 'Entry Protocol 5 + 증상 + 시간 정보 + 클라이언트 목표',
    section_basic: '기본 정보',
    section_entry: 'Entry Protocol 5축 측정',
    section_symptoms: '증상 호소',
    section_temporal: '시간 정보',
    section_goals: '클라이언트 목표',
    section_biomarkers: '바이오마커 (선택)',
    label_initials: '이니셜',
    label_birth_year: '출생연도',
    label_gender: '성별',
    label_referral: '의뢰 출처',
    label_concerns: '주 호소',
    label_medications: '복용 약물',
    label_sustained_attention: '지속 주의력',
    label_working_memory: '작업 기억',
    label_emotional_regulation: '정서 조절',
    label_time_awareness: '시간 감각',
    label_self_awareness: '자기 인지',
    label_primary_axis: '주 임상축',
    label_motivation: '동기',
    label_barriers: '장애 요인',
    label_onset_age: '발병 연령',
    label_course: '경과',
    label_duration: '지속 기간 (월)',
    label_pervasiveness: '편재성',
    label_stress_triggered: '스트레스 유발',
    label_family_history: '가족력',
    btn_run_assessment: '평가 실행',
    btn_save_draft: '임시 저장',

    // result.html
    result_title: '임상 리포트',
    result_subtitle: 'Decision Catcher 분석 결과',
    section_clinical_scores: '임상 점수',
    section_dde: '감별 진단',
    section_decomp: '공존 진단 분해',
    section_simulator: '인지 시뮬레이션',
    section_safety: '안전 플래그',
    section_recommendation: '추천 카드',
    label_primary_dx: '주 진단',
    label_secondary_dx: '부 진단',
    label_confidence: '진단 신뢰도',
    label_pattern: '공존 패턴',
    label_priority: '치료 우선순위',
    label_rationale: '근거',
    btn_view_protocol: '프로토콜 보기',
    btn_generate_protocol: '프로토콜 생성',

    // outcome.html
    outcome_title: '4주 Outcome 평가',
    outcome_subtitle: '훈련 후 변화 측정 + Adaptive Re-routing',
    section_before: '훈련 전',
    section_after: '훈련 후',
    section_self_report: '자가 보고',
    label_improvement: '주관적 개선도',
    label_satisfaction: '만족도',
    btn_calc_reroute: 'Re-routing 계산',
    btn_save_outcome: 'Outcome 저장',

    // protocol.html
    protocol_title: '훈련 프로토콜',
    protocol_subtitle: '4-8주 적응형 훈련 계획',
    label_axis_selected: '선택 축',
    label_weeks: '훈련 주수',
    label_sessions: '세션 자료',
    label_progression: '주간 진행',
    label_success_criteria: '성공 기준',

    // manual / beta-guide / feedback - 공통
    manual_title: '클라이언트 매뉴얼',
    manual_subtitle: 'Decision Catcher 베타 참여 가이드',
    beta_guide_title: '베타 가이드',
    beta_guide_subtitle: '베타 프로그램 안내',
    feedback_title: '피드백',
    feedback_subtitle: '의견을 들려주세요',
    label_category: '카테고리',
    label_rating: '평점',
    label_comment: '코멘트',
    btn_send_feedback: '피드백 전송',

    // beta-pending.html
    pending_title: '신청 대기 중',
    pending_subtitle: '동의 절차 진행 중',
    pending_check_email: '이메일을 확인해 주세요',
    pending_status_label: '현재 상태',
    pending_back_home: '홈으로',
  },
  en: {
    // Common menu
    home: 'Home',
    new_client: 'New Client',
    outcome: '4-week Outcome',
    manual: 'Manual',
    beta_guide: 'Beta Guide',
    admin: '← Admin',
    logout: 'Logout',
    lang_toggle: '한국어',
    clinician_manual: 'Clinician Manual',

    // Common buttons
    btn_start: 'Start',
    btn_next: 'Next',
    btn_back: 'Back',
    btn_save: 'Save',
    btn_submit: 'Submit',
    btn_cancel: 'Cancel',
    btn_close: 'Close',
    btn_confirm: 'Confirm',
    btn_continue: 'Continue',
    btn_reset: 'Reset',
    btn_download: 'Download',
    btn_print: 'Print',

    // index.html - Hero
    badge_v7: 'CNA v7.0 · Round 7-10 Integrated',
    site_title: 'Decision Catcher',
    site_subtitle: 'Differential Dx + Comorbidity + Adaptive Training',
    site_company: 'Boston Neuromind LLC · Catcher Navigator Algorithm',
    btn_start_assessment: 'Start New Client Assessment',
    btn_view_manual: 'View Manual',

    // index.html - Why
    why_title: 'Why This System',
    why_p1_intro: 'Added',
    why_p1_highlight: 'Differential & Comorbidity Diagnosis',
    why_p1_outro: 'to the existing 5-axis mapping system (CNA v6). Decomposes how ADHD, GAD, and MDD each contribute to a client\'s clinical scores, and adaptively provides matching training cards.',
    why_principle_label: 'Core Principle:',
    why_principle_text: 'The same "Attention 0.39" score requires completely different treatment strategies when ADHD is primary vs. GAD primary. SSRI alone for unrecognized ADHD is ineffective (McIntosh et al. 2009). Diagnostic accuracy is the foundation of treatment efficacy.',

    // index.html - v7 modules
    v7_modules_title: 'v7 Added Modules (Round 7-10)',
    module1_title: '① Differential Diagnosis Engine',
    module1_desc: 'Symptom complaints + 5 cognitive axes + biomarkers + temporal data → Bayesian differential diagnosis',
    module1_small: 'DSM-5-TR canonical pattern matching',
    module2_title: '② Comorbidity Decomposition',
    module2_desc: 'Decomposes clinical scores by diagnostic source (e.g., Attention 0.39 = ADHD 0.25 + GAD 0.10 + MDD 0.04)',
    module3_title: '③ Cognitive Simulator',
    module3_desc: '"If we improve this cognitive axis, how will the clinical axis change?" Counterfactual simulation',
    module4_title: '④ Adaptive Re-routing',
    module4_desc: '4-week outcome → comparison with expected response pattern → auto-reconstruction of diagnosis on mismatch',

    // index.html - 5-Axis
    axis_title: '5-Axis Clinical Domains',
    axis_attention: 'Attention',
    axis_attention_desc: 'CPT, ASRS',
    axis_learning: 'Learning Efficiency',
    axis_learning_desc: 'N-back, retention',
    axis_peak: 'Peak Performance',
    axis_peak_desc: 'Time estimation, HRV',
    axis_anxiety: 'Anxiety Management',
    axis_anxiety_desc: 'HRV, GAD-7',
    axis_depression: 'Mood Stability',
    axis_depression_desc: 'PHQ-9, BA count',

    // index.html - Evidence
    evidence_title: 'Clinical Evidence',
    evidence_col1: 'Mapping / Algorithm',
    evidence_col2: 'Clinical Evidence',
    evidence_wm: 'Working Memory → Learning (r=0.43)',
    evidence_wm_src: 'Meta-analysis, n=7947',
    evidence_ei: 'Emotional Intelligence → Academic (r=0.39)',
    evidence_ei_src: 'EI-AP meta-analysis 2023',
    evidence_er: 'Emotion Regulation effect (d=0.605)',
    evidence_er_src: 'Aldao et al. 2010',
    evidence_ai: 'Active Inference clinical application',
    evidence_ai_src: 'Friston 2010-2025',
    evidence_adhd: 'Adult ADHD comorbidity 50-80%',
    evidence_adhd_src: 'Frontiers 2025',
    evidence_temporal: 'Key to differentiation = temporal pattern',
    evidence_temporal_src: 'Multiple',
    evidence_ssri: 'SSRI alone for unrecognized ADHD = failure',
    evidence_ssri_src: 'McIntosh et al. 2009',

    // index.html - Next steps
    next_steps_title: 'Next Steps',
    step1_title: 'New Client Assessment',
    step1_desc: 'Entry Protocol 5 + symptoms + temporal data + client goals',
    step2_title: 'Clinical Report Review',
    step2_desc: '5-axis scores + DDE + Decomposition + Simulator',
    step3_title: 'Training Protocol Execution',
    step3_desc: '4-8 weeks, system recommendation + clinician override',
    step4_title: '4-week Outcome Input',
    step4_desc: 'Adaptive Re-routing auto-execution',
    btn_get_started: 'Get Started',

    // Footer
    footer_company: 'Boston Neuromind LLC · CNA v7.0.0 · 2026',
    footer_author: 'Alex Kwon (BCN, PhD)',

    // clinician.html
    clinician_title: 'New Client Assessment',
    clinician_subtitle: 'Entry Protocol 5 + symptoms + temporal + client goals',
    section_basic: 'Basic Info',
    section_entry: 'Entry Protocol 5-Axis Measurement',
    section_symptoms: 'Symptom Complaints',
    section_temporal: 'Temporal Info',
    section_goals: 'Client Goals',
    section_biomarkers: 'Biomarkers (optional)',
    label_initials: 'Initials',
    label_birth_year: 'Birth Year',
    label_gender: 'Gender',
    label_referral: 'Referral Source',
    label_concerns: 'Primary Concerns',
    label_medications: 'Medications',
    label_sustained_attention: 'Sustained Attention',
    label_working_memory: 'Working Memory',
    label_emotional_regulation: 'Emotional Regulation',
    label_time_awareness: 'Time Awareness',
    label_self_awareness: 'Self Awareness',
    label_primary_axis: 'Primary Clinical Axis',
    label_motivation: 'Motivation',
    label_barriers: 'Barriers',
    label_onset_age: 'Onset Age',
    label_course: 'Course',
    label_duration: 'Duration (months)',
    label_pervasiveness: 'Pervasiveness',
    label_stress_triggered: 'Stress Triggered',
    label_family_history: 'Family History',
    btn_run_assessment: 'Run Assessment',
    btn_save_draft: 'Save Draft',

    // result.html
    result_title: 'Clinical Report',
    result_subtitle: 'Decision Catcher Analysis Results',
    section_clinical_scores: 'Clinical Scores',
    section_dde: 'Differential Diagnosis',
    section_decomp: 'Comorbidity Decomposition',
    section_simulator: 'Cognitive Simulation',
    section_safety: 'Safety Flags',
    section_recommendation: 'Card Recommendations',
    label_primary_dx: 'Primary Diagnosis',
    label_secondary_dx: 'Secondary Diagnoses',
    label_confidence: 'Diagnostic Confidence',
    label_pattern: 'Comorbidity Pattern',
    label_priority: 'Treatment Priority',
    label_rationale: 'Rationale',
    btn_view_protocol: 'View Protocol',
    btn_generate_protocol: 'Generate Protocol',

    // outcome.html
    outcome_title: '4-Week Outcome Evaluation',
    outcome_subtitle: 'Post-training change measurement + Adaptive Re-routing',
    section_before: 'Before Training',
    section_after: 'After Training',
    section_self_report: 'Self-Report',
    label_improvement: 'Subjective Improvement',
    label_satisfaction: 'Satisfaction',
    btn_calc_reroute: 'Calculate Re-routing',
    btn_save_outcome: 'Save Outcome',

    // protocol.html
    protocol_title: 'Training Protocol',
    protocol_subtitle: '4-8 week adaptive training plan',
    label_axis_selected: 'Selected Axis',
    label_weeks: 'Training Weeks',
    label_sessions: 'Session Details',
    label_progression: 'Weekly Progression',
    label_success_criteria: 'Success Criteria',

    // manual / beta-guide / feedback
    manual_title: 'Client Manual',
    manual_subtitle: 'Decision Catcher Beta Participation Guide',
    beta_guide_title: 'Beta Guide',
    beta_guide_subtitle: 'Beta Program Overview',
    feedback_title: 'Feedback',
    feedback_subtitle: 'Share your thoughts',
    label_category: 'Category',
    label_rating: 'Rating',
    label_comment: 'Comment',
    btn_send_feedback: 'Send Feedback',

    // beta-pending.html
    pending_title: 'Application Pending',
    pending_subtitle: 'Consent process in progress',
    pending_check_email: 'Please check your email',
    pending_status_label: 'Current Status',
    pending_back_home: 'Back to Home',
    // === result.html ===
    result_page_title: 'Assessment Results',
    btn_protocol: 'Protocol',
    no_data_msg: 'No assessment data.',
    no_data_link: 'New Client Assessment',
    no_data_continue: ' to start.',
    next_steps_h: 'Next Steps',
    btn_protocol_sim: 'Protocol Details + Simulation',
    btn_save_pdf: 'Save as PDF',
    client_label: 'Client',
    selected_area_label: 'Client Selected Area:',
    motiv_label: 'Motivation:',
    session_label: 'Session:',
    safety_h: 'Safety Protocol Triggered',
    safety_count_suffix: ' flag(s)',
    severity_label: 'severity:',
    triggered_label: 'Triggered by:',
    action_label: 'Action:',
    imminent_warning: '⚠️ Imminent risk — Stop session + Emergency action required',
    section1_h: '① Fischer Cognitive 5-Axis',
    section2_h: '② Clinical 5-Axis Prediction',
    col_area: 'Area',
    col_score: 'Score',
    col_tier: 'Tier',
    col_priority: 'Priority',
    col_top_cog: 'Top Contributing Cognitive Axis',
    section3_h: '③ Differential Diagnosis Engine (v7)',
    primary_label: 'Primary:',
    secondary_label: 'Secondary:',
    none_text: 'None',
    comorbidity_pattern_label: 'Comorbidity pattern:',
    single_dx: 'Single diagnosis',
    coverage_text_pre: '(coverage ',
    coverage_text_post: '%)',
    confidence_label: 'Confidence:',
    treatment_rationale_label: 'Treatment rationale:',
    flagged_review_label: '⚠ Clinician review required:',
    dx_distribution_h: 'Diagnostic Hypothesis Distribution',
    primary_marker: '★ Primary: ',
    secondary_marker: '• Secondary: ',
    symptom_match_label: 'Symptom Match (40%)',
    cognitive_match_label: 'Cognitive Match (20%)',
    biomarker_match_label: 'Biomarker (10%)',
    temporal_match_label: 'Temporal (30%)',
    met_label: '✓ Met:',
    missed_label: '✗ Missed:',
    section4_h: '④ Comorbidity Decomposition (v7)',
    primary_source_label: 'Primary source:',
    decomp_axes_h: 'Clinical 5-Axis Source Decomposition',
    score_word: 'score',
    impairment_word: 'impairment',
    explanation_word: 'explained',
    contribution_word: 'contribution',
    posterior_word: 'posterior',
    treatment_target_word: 'Treatment target:',
    residual_word: 'Residual:',
    intervention_priority_h: 'Intervention Priority',
    primary_impact_label: 'Primary impact:',
    section5_h: '⑤ Intervention Priority — Counterfactual Simulator (v7)',
    col_rank: 'Rank',
    col_cog_axis: 'Cognitive Axis',
    col_level_change: 'Level Change',
    col_total_improvement: 'Total Clinical Improvement',
    col_primary_benefit: 'Primary Effect',
    section6_h_pre: '⑥ Target Level Auto-Recommendation (',
    section6_h_mid: ' score ≥ ',
    section6_h_post: ')',
    current_score_label: 'Current score:',
    target_score_label: 'Target:',
    col_current_level: 'Current Level',
    col_target_level: 'Target Level',
    col_delta: 'Delta',
    col_feasibility: 'Feasibility',
    feasible_text: '✓ Feasible',
    infeasible_text_pre: '✗ Alone insufficient (max ',
    infeasible_text_post: ')',
    not_alone_text: 'Alone insufficient',
    section7_h: '⑦ System Recommendation (Free Energy)',
    emergency_phase_text: '⚠ Emergency phase active — Pragmatic priority',
    dx_aligned_text: '✓ Diagnosis-aligned cards prioritized',
    col_card_id: 'Card ID',
    col_description: 'Description',
    section8_h_pre: '⑧ Protocol Preview (',
    section8_h_weeks: ' weeks, total ',
    section8_h_post: ' sessions)',
    area_label: 'Area:',
    progression_label: 'Progression:',
    default_progression: 'Weekly gradual intensification',
    section9_h_pre: '⑨ Protocol Effect Simulation (',
    section9_h_weeks: ' weeks, uncertainty ',
    section9_h_post: '%)',
    expected_cog_change_h: 'Expected Cognitive Change',
    expected_clin_change_h: 'Expected Clinical Change',
    col_now: 'Current',
    col_expected: 'Expected',
    col_change: 'Change',
    sim_assumptions: 'Simulation Assumptions',
    // === outcome.html ===
    outcome_page_title: '4-Week Outcome + Re-routing',
    btn_assessment_result: 'Results',
    btn_protocol_short: 'Protocol',
    outcome_intro_strong: 'After 4-week session ends',
    outcome_intro_text: 'Input outcome → Adaptive Re-routing auto-executes (v7)',
    section_session_info: 'Session Info',
    label_episode_id: 'Episode ID',
    episode_id_help: 'Data received from previous assessment',
    label_primary_intervention: 'Primary Intervention Area',
    label_applied_cards: 'Applied Card IDs (comma)',
    section_before_data: 'Before Training',
    section_after_data: '4-Week After Training',
    cog_5axis_h: 'Cognitive 5-Axis',
    clin_5axis_h: 'Clinical 5-Axis Scores',
    section_prev_dx: 'Previous Diagnosis (required)',
    label_prev_dx_json: 'Previous Differential Diagnosis Result (JSON)',
    prev_dx_help: 'Copy the DDE result from previous assessment (auto-saved in sessionStorage)',
    btn_load_prev: 'Auto-fill from Previous Assessment',
    btn_run_reroute: 'Run Re-routing',
    no_prev_assessment: 'No previous assessment data',
    json_err_prefix: 'Previous diagnosis JSON format error:',
    api_err_prefix: 'API error:',
    reroute_result_h: 'Diagnosis Re-routing Result',
    prev_to_updated_h: 'Previous → Updated',
    changed_label: 'Changed',
    change_type_label: 'Change Type',
    response_pattern_label: 'Response Pattern',
    posterior_mag_label: 'Posterior Update Magnitude',
    yes_word: 'Yes',
    no_word: 'No',
    clinician_data_label: 'Clinician Note:',
    clinician_review_needed: '⚠ Clinician review required',
    dx_changed_text: 'Diagnosis changed.',
    btn_re_assess: 'Re-assess with New Diagnosis',
    dx_unchanged_text: 'Diagnosis maintained. Continue current protocol or new protocol.',
    btn_protocol_data: 'Protocol Data',
    // === protocol.html ===
    protocol_page_title: 'Training Protocol',
    no_protocol_data: 'No protocol data.',
    no_protocol_link: 'New Client Assessment',
    no_protocol_continue: ' to start.',
    session_progress_h: 'Session Workflow',
    each_session_label: 'Each session:',
    session_start: 'Start (5 min): HRV measurement, mood check',
    session_run: 'Cards (15-60 min): System-recommended or clinician-override',
    session_end: 'End (5 min): HRV re-measure, OMR response',
    after_4w_label: 'After 4 weeks →',
    btn_outcome_reroute: 'Input Outcome + Re-routing',
    protocol_data_h: 'Protocol Data',
    p_period_label: 'Duration:',
    p_total_sessions: 'Total Sessions:',
    p_progression_method: 'Progression:',
    weekly_data_h: 'Weekly Schedule',
    col_session: 'Session',
    col_week: 'Week',
    col_day: 'Day',
    col_time: 'Time',
    col_cards: 'Cards',
    success_criteria_h: 'Success Criteria',
    measurement_data_h: 'Measurement Schedule',
    expected_effect_sim_h: 'Expected Effect Simulation (v7)',
    uncertainty_label: 'Uncertainty:',
    cog_5axis_expected_h: 'Expected Cognitive 5-Axis Change',
    clin_5axis_expected_h: 'Expected Clinical 5-Axis Change',
    sim_assumptions_h: 'Simulation Assumptions',
    minutes_suffix: 'min',
    // === clinician.html ===
    clinician_page_title: '새 클라이언트 평가',
    workflow_label: '회기 1 워크플로 (75-105분)',
    workflow_desc: 'Step 1: 클라이언트 등록 → Step 2: Entry Protocol 5 측정 → Step 3: 증상 자료 → Step 4: 시간 정보 인터뷰 (v7 NEW) → Step 5: 클라이언트 목표',
    step1_h: 'Step 1: 클라이언트 등록',
    client_id_label: '클라이언트 ID',
    client_id_help: '이니셜 + 번호 (예: AK001)',
    session_num_label: '회기 번호',
    session_num_help: '첫 회기 = 0',
    step2_h: 'Step 2: Fischer 인지 5축 측정',
    step2_desc: 'Entry Protocol 5 측정 결과 → Fischer Level (L7.0-L13.0)',
    cog_sustained: '지속 주의력 (CPT)',
    cog_working: '작업 기억 (N-back)',
    cog_emotional: '정서 조절 (HRV)',
    cog_time: '시간 감각',
    cog_self: '자기 인지',
    biomarker_h: '바이오마커 (선택)',
    bio_cpt_om: 'CPT Omissions Z-score',
    bio_cpt_rt: 'CPT RT Variability',
    bio_hrv: 'HRV RMSSD (ms)',
    bio_nback: 'N-back 정확도 (0-1)',
    bio_time: '시간 추정 오차 %',
    step3_h: 'Step 3: 증상 자료 (0.0 - 1.0)',
    step3_desc_part1: '중요:',
    step3_desc_part2: '클라이언트가 호소하는 증상 강도. DDE 입력의 핵심 (40% 가중치).',
    sym_inatt: '부주의 (Inattention)',
    sym_distract: '분산성 (Distractibility)',
    sym_exec: '실행 기능 저하',
    sym_anx_somatic: '신체 불안',
    sym_anx_cog: '인지 불안',
    sym_low_mood: '기분 저하',
    sym_low_motiv: '동기 저하',
    sym_social: '사회적 위축',
    step4_h: 'Step 4 (v7 NEW): 시간 정보 인터뷰 ⭐',
    step4_desc: 'DDE 정확도의 핵심. 8문항 (감별 진단 30% 가중치). 모르는 항목은 비워두세요 — 부정확보다 빈 자료가 낫습니다.',
    temp_onset_age_label: '1. 발병 나이',
    temp_onset_age_ph: '예: 8',
    temp_onset_age_help: '"증상이 처음 나타난 나이?" 12세 미만 = ADHD signal',
    temp_onset_cat_label: '2. 발병 단계',
    opt_unknown: '모름',
    opt_childhood: '아동기 (<12세)',
    opt_adolescence: '청소년기 (12-18세)',
    opt_adult: '성인기 (18+)',
    opt_any_age: '어느 나이든',
    temp_course_label: '3. 경과',
    opt_chronic: '만성 (쭉 지속)',
    opt_episodic: '에피소드 (왔다 갔다)',
    opt_fluctuating: '변동 (강도 차이)',
    temp_duration_label: '4. 지속 기간 (개월)',
    temp_duration_help: 'MDD 0.5+, GAD 6+, ADHD 60+',
    temp_pervasive_label: '5. 광범위성',
    opt_cross_setting: '모든 환경 (ADHD signal)',
    opt_context_dep: '특정 상황만 (anxiety signal)',
    opt_all_setting: '전반적 (depression)',
    temp_stress_label: '6. 스트레스 유발?',
    opt_yes_stress: '예 (anxiety/depression signal)',
    opt_no_stress: '아니오 (ADHD signal)',
    temp_family_label: '7. 가족력 (콤마 구분)',
    temp_family_ph: '예: father_ADHD, mother_GAD',
    temp_treatment_label: '8. 이전 치료 반응 (JSON)',
    temp_treatment_help: 'SSRI 무반응 + stimulant 좋은 반응 = ADHD strong signal',
    step5_h: 'Step 5: 클라이언트 목표',
    primary_axis_label: '가장 개선하고 싶은 영역',
    opt_attention: '주의력',
    opt_learning: '학습 효율',
    opt_peak: '수행 최적화',
    opt_anxiety: '불안 관리',
    opt_depression: '기분 안정',
    motivation_label: '동기 수준 (0.0 - 1.0)',
    barriers_label: '인식된 장애물',
    barriers_ph: '예: 시간 부족, 가족 협조 어려움',
    btn_run_full_assess: '평가 실행 (DDE + Decomposition + Simulator)',
    processing: '처리 중...',
    processing_desc: 'CNA v7 자료 분석 중 (보통 2-5초)',
    // === result.html ===
    result_page_title: '평가 결과',
    btn_protocol: '프로토콜',
    no_data_msg: '평가 항목 없음.',
    no_data_link: '새 클라이언트 평가',
    no_data_continue: '를 시작해주세요.',
    next_steps_h: '다음 단계',
    btn_protocol_sim: '프로토콜 자료 + 시뮬레이션',
    btn_save_pdf: 'PDF 저장',
    client_label: '클라이언트',
    selected_area_label: '클라이언트 선택 영역:',
    motiv_label: '동기:',
    session_label: '회기:',
    safety_h: '안전 프로토콜 catch',
    safety_count_suffix: '개',
    severity_label: 'severity:',
    triggered_label: 'Triggered by:',
    action_label: '조치:',
    imminent_warning: '⚠️ Imminent 자료 — 회기 중단 + 응급 조치 필요',
    section1_h: '① Fischer 인지 5축',
    section2_h: '② 임상 5축 예측표',
    col_area: '영역',
    col_score: '점수',
    col_tier: '단계',
    col_priority: '우선',
    col_top_cog: '주요 기여 인지축',
    section3_h: '③ Differential Diagnosis Engine (v7)',
    primary_label: 'Primary:',
    secondary_label: 'Secondary:',
    none_text: '없음',
    comorbidity_pattern_label: 'Comorbidity pattern:',
    single_dx: '단일 진단',
    coverage_text_pre: '(공존률 ',
    coverage_text_post: '%)',
    confidence_label: 'Confidence:',
    treatment_rationale_label: '치료 자료:',
    flagged_review_label: '⚠ 임상가 검토 자료:',
    dx_distribution_h: '진단 가설 분포',
    primary_marker: '★ Primary: ',
    secondary_marker: '• Secondary: ',
    symptom_match_label: '증상 매칭 (40%)',
    cognitive_match_label: '인지 매칭 (20%)',
    biomarker_match_label: '바이오마커 (10%)',
    temporal_match_label: '시간 정보 (30%)',
    met_label: '✓ 충족:',
    missed_label: '✗ 미충족:',
    section4_h: '④ Comorbidity Decomposition (v7)',
    primary_source_label: 'Primary source:',
    decomp_axes_h: '임상 5축 source 분해',
    score_word: '점수',
    impairment_word: '약화',
    explanation_word: '설명력',
    contribution_word: '기여',
    posterior_word: 'posterior',
    treatment_target_word: '치료 target:',
    residual_word: '잔차:',
    intervention_priority_h: '개입 우선순위',
    primary_impact_label: '주 영향:',
    section5_h: '⑤ 개입 우선순위 — Counterfactual Simulator (v7)',
    col_rank: '순위',
    col_cog_axis: '인지축',
    col_level_change: 'Level 변경',
    col_total_improvement: '전체 임상 개선',
    col_primary_benefit: '주 효과',
    section6_h_pre: '⑥ 목표 Level 자동 추천 (',
    section6_h_mid: ' 점수 ≥ ',
    section6_h_post: ')',
    current_score_label: '현재 점수:',
    target_score_label: '목표:',
    col_current_level: '현재 Level',
    col_target_level: '필요 Level',
    col_delta: '증가량',
    col_feasibility: '달성 가능성',
    feasible_text: '✓ 가능',
    infeasible_text_pre: '✗ 단독 불가 (최대 ',
    infeasible_text_post: ')',
    not_alone_text: '단독 불가',
    section7_h: '⑦ 시스템 추천 (Free Energy 자료)',
    emergency_phase_text: '⚠ Emergency phase 활성 — Pragmatic 우선 자료',
    dx_aligned_text: '✓ 진단 자료 카드 우선 자료',
    col_card_id: '카드 ID',
    col_description: '설명',
    section8_h_pre: '⑧ 프로토콜 미리보기 (',
    section8_h_weeks: '주, 총 ',
    section8_h_post: '회기)',
    area_label: '영역:',
    progression_label: '진행:',
    default_progression: '주차별 점진 강화',
    section9_h_pre: '⑨ 프로토콜 효과 시뮬레이션 (',
    section9_h_weeks: '주, uncertainty ',
    section9_h_post: '%)',
    expected_cog_change_h: '예상 인지 자료 변화',
    expected_clin_change_h: '예상 임상 자료 변화',
    col_now: '현재',
    col_expected: '예상',
    col_change: '변화',
    sim_assumptions: '시뮬레이션 가정 자료',
    // === outcome.html ===
    outcome_page_title: '4주 Outcome + Re-routing',
    btn_assessment_result: '평가 결과',
    btn_protocol_short: '프로토콜',
    outcome_intro_strong: '4주 회기 종료 후',
    outcome_intro_text: 'Outcome 입력 → Adaptive Re-routing 자동 실행 (v7)',
    section_session_info: '회기 자료',
    label_episode_id: 'Episode ID',
    episode_id_help: '이전 평가에서 받은 자료',
    label_primary_intervention: 'Primary 개입 영역',
    label_applied_cards: '적용한 카드 IDs (콤마)',
    section_before_data: '이전 자료 (Before)',
    section_after_data: '4주 후 자료 (After)',
    cog_5axis_h: '인지 5축',
    clin_5axis_h: '임상 5축 점수',
    section_prev_dx: '이전 진단 자료 (필수)',
    label_prev_dx_json: '이전 평가의 Differential Diagnosis 결과 (JSON)',
    prev_dx_help: '이전 평가 페이지의 DDE 결과를 그대로 복사하세요 (sessionStorage에 자동 저장됨)',
    btn_load_prev: '이전 평가 항목 자동 입력',
    btn_run_reroute: 'Re-routing 실행',
    no_prev_assessment: '이전 평가 항목 없음',
    json_err_prefix: '이전 진단 JSON 형식 catch 안 됨:',
    api_err_prefix: 'API 오류:',
    reroute_result_h: '진단 재구성 결과',
    prev_to_updated_h: '이전 → 갱신',
    changed_label: '변경 여부',
    change_type_label: '변경 유형',
    response_pattern_label: '반응 패턴',
    posterior_mag_label: 'Posterior 변화 magnitude',
    yes_word: '예',
    no_word: '아니오',
    clinician_data_label: '임상가 자료:',
    clinician_review_needed: '⚠ 임상가 검토 필요',
    dx_changed_text: '진단이 변경되었습니다.',
    btn_re_assess: '새 진단으로 평가 재실행',
    dx_unchanged_text: '진단 유지. 현재 프로토콜 계속 또는 새 프로토콜 자료.',
    btn_protocol_data: '프로토콜 자료',
    // === protocol.html ===
    protocol_page_title: '훈련 프로토콜',
    no_protocol_data: '프로토콜 자료 없음.',
    no_protocol_link: '새 클라이언트 평가',
    no_protocol_continue: '부터 시작하세요.',
    session_progress_h: '회기 진행 자료',
    each_session_label: '각 회기:',
    session_start: '시작 (5분): HRV 측정, 기분 체크',
    session_run: '카드 실행 (15-60분): 시스템 추천 카드 또는 임상가 override',
    session_end: '종료 (5분): HRV 재측정, OMR 응답',
    after_4w_label: '4주 후 →',
    btn_outcome_reroute: 'Outcome 입력 + Re-routing',
    protocol_data_h: '프로토콜 자료',
    p_period_label: '기간:',
    p_total_sessions: '총 회기:',
    p_progression_method: '진행 방식:',
    weekly_data_h: '주별 자료',
    col_session: '회기',
    col_week: '주차',
    col_day: '요일',
    col_time: '시간',
    col_cards: '카드',
    success_criteria_h: '성공 기준',
    measurement_data_h: '측정 자료',
    expected_effect_sim_h: '예상 효과 시뮬레이션 (v7)',
    uncertainty_label: 'Uncertainty:',
    cog_5axis_expected_h: '인지 5축 예상 변화',
    clin_5axis_expected_h: '임상 5축 예상 변화',
    sim_assumptions_h: '시뮬레이션 가정',
    minutes_suffix: '분',
  },
};

function getLang() {
  return localStorage.getItem(CONFIG.langKey) || CONFIG.defaultLang;
}

function setLang(lang) {
  localStorage.setItem(CONFIG.langKey, lang);
  applyLang();
}

function toggleLang() {
  const current = getLang();
  setLang(current === 'ko' ? 'en' : 'ko');
}

function t(key) {
  const lang = getLang();
  return (I18N[lang] && I18N[lang][key]) || (I18N.ko[key] || key);
}

function applyLang() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.setAttribute('placeholder', t(key));
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    el.setAttribute('title', t(key));
  });
  document.documentElement.lang = getLang();
}

// ============================================================
// 인증
// ============================================================

function checkAuth() {
  return sessionStorage.getItem(CONFIG.passwordKey) === '1';
}

function tryLogin(password, onSuccess, onError) {
  if (password === CONFIG.password) {
    sessionStorage.setItem(CONFIG.passwordKey, '1');
    if (onSuccess) onSuccess();
  } else {
    if (onError) onError('Wrong password');
  }
}

function logout() {
  sessionStorage.removeItem(CONFIG.passwordKey);
  window.location.href = '/';
}

function requireAuth() {
  if (!checkAuth()) {
    const overlay = document.createElement('div');
    overlay.className = 'login-overlay';
    overlay.innerHTML = `
      <div class="login-box">
        <h2>Decision Catcher</h2>
        <p style="color:#5a4a35;margin-bottom:20px;">Admin password 필요</p>
        <input type="password" id="loginPw" placeholder="Password" autofocus>
        <button id="loginBtn">Enter</button>
        <div class="login-err" id="loginErr"></div>
      </div>
    `;
    document.body.appendChild(overlay);

    const pwInput = document.getElementById('loginPw');
    const errMsg = document.getElementById('loginErr');
    const goBtn = document.getElementById('loginBtn');

    function attempt() {
      tryLogin(pwInput.value,
        () => { overlay.remove(); },
        (msg) => { errMsg.textContent = msg; }
      );
    }
    goBtn.addEventListener('click', attempt);
    pwInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') attempt();
    });
  }
}

// ============================================================
// State 관리
// ============================================================

const State = {
  save(key, data) {
    sessionStorage.setItem('decision_' + key, JSON.stringify(data));
  },
  load(key) {
    const raw = sessionStorage.getItem('decision_' + key);
    return raw ? JSON.parse(raw) : null;
  },
  clear(key) {
    sessionStorage.removeItem('decision_' + key);
  },
  clearAll() {
    Object.keys(sessionStorage)
      .filter(k => k.startsWith('decision_'))
      .forEach(k => sessionStorage.removeItem(k));
  },
};

// ============================================================
// API 호출
// ============================================================

async function callAPI(endpoint, method = 'POST', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  try {
    const res = await fetch(CONFIG.apiBase + endpoint, options);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`API ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    console.error('API call failed:', err);
    throw err;
  }
}

// ============================================================
// 점수 변환 자료
// ============================================================

function scoreTier(score) {
  const lang = getLang();
  if (lang === 'en') {
    if (score >= 0.75) return { name: 'Excellent', class: 'score-excellent' };
    if (score >= 0.60) return { name: 'Good', class: 'score-good' };
    if (score >= 0.45) return { name: 'Average', class: 'score-average' };
    if (score >= 0.30) return { name: 'Caution', class: 'score-caution' };
    return { name: 'Priority', class: 'score-priority' };
  }
  if (score >= 0.75) return { name: '매우 우수', class: 'score-excellent' };
  if (score >= 0.60) return { name: '우수', class: 'score-good' };
  if (score >= 0.45) return { name: '보통', class: 'score-average' };
  if (score >= 0.30) return { name: '주의', class: 'score-caution' };
  return { name: '임상 우선', class: 'score-priority' };
}

function clinicalAxisKo(axis) {
  const lang = getLang();
  if (lang === 'en') {
    const en = {
      attention: 'Attention',
      learning: 'Learning Efficiency',
      peak_performance: 'Peak Performance',
      anxiety: 'Anxiety Management',
      depression: 'Mood Stability',
    };
    return en[axis] || axis;
  }
  const map = {
    attention: '주의력',
    learning: '학습 효율',
    peak_performance: '수행 최적화',
    anxiety: '불안 관리',
    depression: '기분 안정',
  };
  return map[axis] || axis;
}

function cognitiveAxisKo(axis) {
  const lang = getLang();
  if (lang === 'en') {
    const en = {
      sustained_attention: 'Sustained Attention',
      working_memory: 'Working Memory',
      emotional_regulation: 'Emotional Regulation',
      time_awareness: 'Time Awareness',
      self_awareness: 'Self Awareness',
    };
    return en[axis] || axis;
  }
  const map = {
    sustained_attention: '지속 주의력',
    working_memory: '작업 기억',
    emotional_regulation: '정서 조절',
    time_awareness: '시간 감각',
    self_awareness: '자기 인지',
  };
  return map[axis] || axis;
}

function diagnosisKo(dx) {
  const lang = getLang();
  if (lang === 'en') {
    const en = {
      adhd_inattentive: 'ADHD Inattentive Type',
      gad: 'Generalized Anxiety Disorder (GAD)',
      mdd: 'Major Depressive Disorder (MDD)',
      learning_optimization: 'Learning Optimization',
      peak_performance: 'Peak Performance',
    };
    return en[dx] || dx;
  }
  const map = {
    adhd_inattentive: 'ADHD 주의력 결핍 우세형',
    gad: '범불안장애 (GAD)',
    mdd: '주요 우울장애 (MDD)',
    learning_optimization: '학습 최적화',
    peak_performance: '수행 최적화',
  };
  return map[dx] || dx;
}

// ============================================================
// Init
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  if (document.body.hasAttribute('data-auth')) {
    requireAuth();
  }

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }

  const langBtn = document.getElementById('langToggleBtn');
  if (langBtn) {
    langBtn.addEventListener('click', toggleLang);
  }

  applyLang();
});
