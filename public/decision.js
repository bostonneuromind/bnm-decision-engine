// ============================================================
// Decision Catcher - Common JavaScript
// Boston Neuromind LLC · CNA v7
// ============================================================

// 설정
const CONFIG = {
  apiBase: '/api',
  passwordKey: 'decisionOK',
  password: 'bnm1#',
};

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
// State 관리 (sessionStorage 자료)
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
// 점수 → 단계 변환
// ============================================================

function scoreTier(score) {
  if (score >= 0.75) return { name: '매우 우수', class: 'score-excellent' };
  if (score >= 0.60) return { name: '우수', class: 'score-good' };
  if (score >= 0.45) return { name: '보통', class: 'score-average' };
  if (score >= 0.30) return { name: '주의', class: 'score-caution' };
  return { name: '임상 우선', class: 'score-priority' };
}

function clinicalAxisKo(axis) {
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
  // 페이지에 data-auth 속성 있으면 인증 자료
  if (document.body.hasAttribute('data-auth')) {
    requireAuth();
  }
  
  // Header logout 버튼 자료
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }
});
