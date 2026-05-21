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
