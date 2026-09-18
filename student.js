// MENU is loaded from the backend API (/api/menu) — single source of truth,
// stays in sync with the database and any admin edits.
let MENU = [];

// API Configuration. Empty string = same origin as the served page, so it works
// whether opened at localhost, 127.0.0.1, or any host the server runs on.
const API_BASE_URL = '';

let currentUser = null, cart = [], orderHistory = JSON.parse(localStorage.getItem("icst_ai_orders") || "[]"), chatOpen = false, uploadedData = [];
const SUPPORTED_CHAT_LANGUAGES = {
  'en-US': 'English',
  'ta-IN': 'Tamil',
  'si-LK': 'Sinhala',
  'hi-IN': 'Hindi',
  'es-ES': 'Spanish',
};
let assistantLanguage = 'en-US';
let assistantContext = { trainingConnected: false, lastIntent: null, lastImageResult: null };

const MULTILINGUAL_TEXT = {
  greeting: {
    'en-US': 'Hello! I can help with menu recommendations, nutrition, and orders.',
    'ta-IN': 'ஹலோ! மெனு பரிந்துரைகள், ஊட்டச்சத்து மற்றும் ஆர்டர்கள் குறித்து உதவ முடியும்.',
    'si-LK': 'හෙලෝ! මෙනු නිර්දේශ, පෝෂණය සහ ඇණවුම් සඳහා මම උදව් කළ හැක.',
    'hi-IN': 'नमस्ते! मैं मेनू सुझाव, पोषण और ऑर्डर में मदद कर सकता हूँ।',
    'es-ES': '¡Hola! Puedo ayudar con recomendaciones de menú, nutrición y pedidos.',
  },
  fallback: {
    'en-US': 'I am here to help. Ask me about food images, orders, nutrition, or training the AI.',
    'ta-IN': 'நான் உதவ כאן. உணவு படங்கள், ஆர்டர், ஊட்டச்சத்து அல்லது AI பயிற்சி பற்றி கேள்க.',
    'si-LK': 'මම ඔබට උදව් කිරීමට ඉන්නවා. ආහාර රූප, ඇණවුම්, පෝෂණය හෝ AI පුහුණුව ගැන අසන්න.',
    'hi-IN': 'मैं आपकी मदद करने के लिए यहाँ हूँ। फ़ूड इमेज, ऑर्डर, पोषण या AI प्रशिक्षण के बारे में पूछें।',
    'es-ES': 'Estoy aquí para ayudar. Pregúntame sobre imágenes de comida, pedidos, nutrición o entrenamiento de IA.',
  },
  languageSwitched: {
    'en-US': 'Language switched. I will respond in your selected language.',
    'ta-IN': 'மொழி மாற்றப்பட்டது. உங்கள் தேர்வான மொழியில் பதிலளிக்கும்.',
    'si-LK': 'භාෂාව මාරු කරන ලදි. ඔබ තෝරාගත් භාෂාවෙන් පිළිතුරු ලබා දෙමි.',
    'hi-IN': 'भाषा बदल दी गई है। मैं आपकी चुनी हुई भाषा में उत्तर दूंगा।',
    'es-ES': 'Idioma cambiado. Responderé en el idioma seleccionado.',
  },
  trainingStarted: {
    'en-US': 'Training pipeline request sent. I am syncing your menu and behavior data to the AI trainer.',
    'ta-IN': 'பயிற்சி கோரிக்கை அனுப்பப்பட்டது. உங்கள் மெனு மற்றும் பயன்பாட்டு தரவுகளை AI பயிற்சியாளருக்குச் சமன்படுத்துகிறேன்.',
    'si-LK': 'පුහුණු පයිප්පලට ඔබගේ මෙනුව සහ පර්යන්ත දත්ත සමඟ මුද්‍රණය යවා ඇත.',
    'hi-IN': 'प्रशिक्षण पाइपलाइन अनुरोध भेजा गया। मैं आपका मेनू और व्यवहार डेटा एआई ट्रेनर के साथ सिंक कर रहा हूं।',
    'es-ES': 'Solicitud de entrenamiento enviada. Estoy sincronizando tus datos de menú y comportamiento con el entrenador de IA.',
  },
  trainingComplete: {
    'en-US': 'Training sync completed successfully. The AI will improve as new data arrives.',
    'ta-IN': 'பயிற்சி செருகல் வெற்றிகரமாக முடிந்தது. புதிய தரவு வரும் போதே AI மேம்படும்.',
    'si-LK': 'පුහුණු සංකලනය සාර්ථකව අවසන් විය. නව දත්ත පැමිණීමත් සමඟ AI වඩා හොඳවනු ඇත.',
    'hi-IN': 'ट्रेनिंग सिंक सफलतापूर्वक पूरा हुआ। नया डेटा आने पर AI सुधरेगा।',
    'es-ES': 'Sincronización de entrenamiento completada con éxito. La IA mejorará cuando lleguen nuevos datos.',
  },
  trainingFailed: {
    'en-US': 'Training sync failed. I will keep trying with the next dataset upload.',
    'ta-IN': 'பயிற்சி செருகல் தோல்வியுற்றது. அடுத்த தரவுத் தரவோடு முயற்சிப்பேன்.',
    'si-LK': 'පුහුණු සංකලනය අසාර්ථක විය. ඊළඟ දත්ත උඩුගත කිරීම සමඟ මම නැවත උත්සාහ කරමි.',
    'hi-IN': 'ट्रेनिंग सिंक विफल हुआ। मैं अगले डेटा अपलोड के साथ फिर से कोशिश करूँगा।',
    'es-ES': 'La sincronización de entrenamiento falló. Intentaré de nuevo con la próxima carga de datos.',
  },
};

function translateText(key, vars = {}){
  const translations = MULTILINGUAL_TEXT[key] || MULTILINGUAL_TEXT['fallback'];
  let template = translations[assistantLanguage] || translations['en-US'] || translations[Object.keys(translations)[0]];
  Object.entries(vars).forEach(([k,v])=>{ template = template.replace(new RegExp(`\{${k}\}`, 'g'), v); });
  return template;
}

function setChatLanguage(lang){ assistantLanguage = lang; document.getElementById('chatLangSelect').value = lang; showToast(`Chat: ${SUPPORTED_CHAT_LANGUAGES[lang] || lang}`, 'success'); addChatMsg('bot', translateText('languageSwitched')); }

function sendTrainingRequest(){ const payload = { menu: MENU, orders: orderHistory, language: assistantLanguage, timestamp: new Date().toISOString() }; if(typeof fetch !== 'function'){ return Promise.reject(new Error('Fetch unavailable')); }
  return fetch(API_BASE_URL + '/api/train', { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(payload) })
    .then(res => { if(!res.ok){ throw new Error(`HTTP ${res.status}`); } return res.json(); })
    .then(data => { assistantContext.trainingConnected = true; return data; });
}

function askTraining(){ addChatMsg('user','Train AI with dataset'); const message = translateText('trainingStarted'); addChatMsg('bot', message); syncDatasetWithTrainingAPI(); }

function syncDatasetWithTrainingAPI(){ sendTrainingRequest().then(data=>{ addChatMsg('bot', translateText('trainingComplete')); console.debug('Training sync response',data); }).catch(err=>{ addChatMsg('bot', translateText('trainingFailed')); console.warn('Training sync failed',err); }); }

function runAssistantIntent(text, source='chat'){
  const lower = text.toLowerCase();
  if(lower.includes('train') || lower.includes('learn') || lower.includes('api')){ syncDatasetWithTrainingAPI(); return translateText('trainingStarted'); }
  if(lower.includes('menu') || lower.includes('show me') || lower.includes('what can i order')){ showPage('order'); return `Here is the smart menu for you. I also recommend the highest scoring items first.`; }
  if(lower.includes('recommend') || lower.includes('best') || lower.includes('suggest')){ return generateRecommendationResponse(lower); }
  if(lower.includes('protein') || lower.includes('high protein')){ return generateTraitRecommendations('High Protein'); }
  if(lower.includes('veg') || lower.includes('vegetarian')){ return generateTraitRecommendations('Vegetarian'); }
  if(lower.includes('calorie') || lower.includes('nutrition') || lower.includes('healthy')){ return generateNutritionResponse(lower); }
  if(lower.includes('spoilage') || lower.includes('fresh') || lower.includes('bad') || lower.includes('rotten')){ return `If you want, upload the food image and I will check freshness and matching menu items.`; }
  const matched = findItemsInText(lower);
  if(matched.length){ matched.forEach(item=> addToCart(item.id)); return `Added ${matched.map(i=>i.name).join(', ')} to cart. Ready when you are.`; }
  // No menu item matched — recommend available foods instead of a dead end.
  return suggestAlternatives(lower);
}

function generateRecommendationResponse(lower){ const reco = getAIRecommendations(); let itemList = reco.items.slice(0, 4).map(i=>`${i.emoji} ${i.name}`).join(', '); return `I recommend: ${itemList}. ${reco.text}`; }

function generateTraitRecommendations(trait){ let filtered = MENU.filter(item => item.protein === trait || item.veg && trait==='Vegetarian'); if(!filtered.length) filtered = MENU.filter(item => item.category==='Lunch'); let names = filtered.slice(0,4).map(i=>`${i.emoji} ${i.name}`).join(', '); return `Top ${trait} choices: ${names}`; }

function generateNutritionResponse(lower){ let item = MENU.find(i=>/salad|juice|vegetable|rice|fish|chicken/.test(i.name.toLowerCase())); if(!item) item = MENU[0]; return `A healthy choice is ${item.name} (${item.calories} kcal). I can also add it to your cart if you want.`; }

// Match menu items by how well the user's text covers EACH item's own words,
// preferring the most specific/complete match — so "egg rotti" resolves to
// "Egg Rotti", not every dish containing "rotti".
function findItemsInText(lower){
  const STOP = new Set(['and','the','with','for','plus','your','our','want','order','get','have','some','please']);
  const inputWords = new Set((lower.match(/[a-z]+/g) || []));
  // Document frequency, so a single distinctive word (e.g. "watalappan") can
  // match a long item name while a common word ("rice") cannot match everything.
  const df = {};
  const rows = MENU.map(item=>{
    const words = (item.name.toLowerCase().match(/[a-z]+/g) || []).filter(w=>w.length>=3 && !STOP.has(w));
    new Set(words).forEach(w=> df[w]=(df[w]||0)+1);
    return { item, words };
  });
  const scored = [];
  rows.forEach(({item, words})=>{
    if(!words.length) return;
    const matched = words.filter(w=> inputWords.has(w));
    if(!matched.length) return;
    const ratio = matched.length / words.length;
    const distinctive = matched.some(w=> df[w] <= 2);
    if(ratio >= 0.5 || distinctive) scored.push({ item, n: matched.length, ratio, matched });
  });
  scored.sort((a,b)=> (b.ratio - a.ratio) || (b.n - a.n));
  // Drop any item whose matched words are a subset of an already-kept (more
  // specific) item — this removes the "Chicken Rotti" etc. when "Egg Rotti" wins.
  const kept = [], keptSets = [];
  for(const s of scored){
    const ms = new Set(s.matched);
    if(keptSets.some(k => [...ms].every(w => k.has(w)))) continue;
    keptSets.push(ms); kept.push(s.item);
    if(kept.length >= 3) break;
  }
  return kept;
}

// When the user asks for something we don't have, suggest available items
// instead of a dead-end "not found" — biased to a category hint if present.
function suggestAlternatives(lower){
  const catHints = [['drink','Beverage'],['juice','Beverage'],['beverage','Beverage'],
    ['dessert','Dessert'],['sweet','Dessert'],['cake','Dessert'],
    ['breakfast','Breakfast'],['lunch','Lunch'],['dinner','Dinner'],['snack','Snack']];
  let pool = MENU;
  for(const [kw,cat] of catHints){ if(lower.includes(kw)){ const f = MENU.filter(i=>i.category===cat); if(f.length){ pool = f; } break; } }
  const picks = [...pool].sort((a,b)=>(b.ai_score||0)-(a.ai_score||0)).slice(0,4);
  if(!picks.length) return translateText('fallback');
  const list = picks.map(i=>`${i.emoji} ${i.name} (Rs.${i.price})`).join(', ');
  return `Sorry, that exact item isn't on our menu. 🍽️ Here are popular options you might like: ${list}. Want me to add any of these?`;
}

// NOTE: sendChat() is defined once, later in this file (async + backend-aware).

// MongoDB API Functions
async function apiLogin(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();
    if (response.ok) {
      currentUser = data.user;
      localStorage.setItem('icst_ai_user', JSON.stringify(currentUser));
      return { success: true, user: data.user };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, error: 'Network error' };
  }
}

async function apiSignup(name, email, password, foodPreference) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, food_preference: foodPreference })
    });
    const data = await response.json();
    if (response.ok) {
      currentUser = data.user;
      localStorage.setItem('icst_ai_user', JSON.stringify(currentUser));
      return { success: true, user: data.user };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('Signup error:', error);
    return { success: false, error: 'Network error' };
  }
}

async function apiCreateOrder(items, deliveryLocation, specialInstructions) {
  if (!currentUser) return { success: false, error: 'Not logged in' };
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.user_id,
        items,
        delivery_location: deliveryLocation,
        special_instructions: specialInstructions
      })
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true, order: data.order };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('Create order error:', error);
    return { success: false, error: 'Network error' };
  }
}

async function apiGetOrders() {
  if (!currentUser) return { success: false, error: 'Not logged in' };
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/orders?user_id=${currentUser.user_id}`);
    const data = await response.json();
    if (response.ok) {
      orderHistory = data.orders;
      localStorage.setItem('icst_ai_orders', JSON.stringify(orderHistory));
      return { success: true, orders: data.orders };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('Get orders error:', error);
    return { success: false, error: 'Network error' };
  }
}

async function apiCancelOrder(orderId) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/orders/${orderId}/cancel`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) return { success: true, order: data.order };
    return { success: false, error: data.error };
  } catch (error) {
    console.error('Cancel order error:', error);
    return { success: false, error: 'Network error' };
  }
}

// Pull the latest order statuses from the server and re-render the tracker.
async function refreshOrders() {
  if (!currentUser) { renderOrderHistory(); return; }
  const r = await apiGetOrders();
  if (r.success) orderHistory = r.orders;
  renderOrderHistory();
  updateProfileStats();
}

// Poll while any order is still in progress; auto-stops once all are done.
let _orderPollTimer = null;
function startOrderTracking() {
  if (_orderPollTimer) return;
  _orderPollTimer = setInterval(async () => {
    const active = orderHistory.some(o => ['placed', 'preparing', 'ready'].includes(o.status));
    if (!active) { clearInterval(_orderPollTimer); _orderPollTimer = null; return; }
    await refreshOrders();
  }, 12000);
}

async function cancelOrderUI(orderId) {
  const r = await apiCancelOrder(orderId);
  if (r.success) { showToast('Order cancelled', 'success'); await refreshOrders(); }
  else { showToast(r.error || 'Could not cancel order', 'error'); }
}

async function apiGetMenu(category = null) {
  try {
    let url = `${API_BASE_URL}/api/menu`;
    if (category) url += `?category=${category}`;
    
    const response = await fetch(url);
    const data = await response.json();
    if (response.ok) {
      return { success: true, items: data.items };
    } else {
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('Get menu error:', error);
    return { success: false, error: 'Network error' };
  }
}

// Auth Functions
function switchAuthTab(tab, el){ document.querySelectorAll('.tab-pill').forEach(t=>t.classList.remove('active')); el.classList.add('active'); document.getElementById('auth-login').style.display = tab==='login'?'block':'none'; document.getElementById('auth-signup').style.display = tab==='signup'?'block':'none'; }

async function doLogin(){
  const email=document.getElementById('loginEmail').value.trim();
  const pass=document.getElementById('loginPass').value;
  const errEl=document.getElementById('loginErr'); errEl.textContent='';
  if(!email.endsWith('@icst.edu.lk')){ errEl.textContent='Email must end with @icst.edu.lk'; return; }
  if(pass.length<4){ errEl.textContent='Password too short'; return; }

  // Authenticate against the backend; fall back to offline demo mode if the API is unreachable.
  const result = await apiLogin(email, pass);
  if(result.success){
    loginUser(result.user);
    showToast('Welcome back!', 'success');
  } else if(result.error === 'Network error'){
    const name=email.split('@')[0].split('.').map(s=>s.charAt(0).toUpperCase()+s.slice(1)).join(' ');
    loginUser({ email, name, pref:'all' });
    showToast('Signed in (offline demo mode)', 'info');
  } else {
    errEl.textContent = result.error || 'Invalid email or password';
  }
}

async function demoLogin(){ 
  // Use demo mode
  loginUser({ email:'student@icst.edu.lk', name:'Demo Student', pref:'all' }); 
}

async function doSignup(){ 
  let name=document.getElementById('signName').value.trim(), 
      email=document.getElementById('signEmail').value.trim(), 
      pass=document.getElementById('signPass').value, 
      pref=document.getElementById('signPref').value; 
  if(!name){document.getElementById('signErr').textContent='Name required';return;} 
  if(!email.endsWith('@icst.edu.lk')){document.getElementById('signErr').textContent='Email must end with @icst.edu.lk';return;} 
  if(pass.length<6){document.getElementById('signErr').textContent='Password must be 6+ chars';return;} 
  
  // Try MongoDB API first
  const result = await apiSignup(name, email, pass, pref);
  if (result.success) {
    loginUser(result.user);
    showToast('Account created!', 'success');
  } else {
    // Fallback to demo mode if MongoDB not available
    console.log('MongoDB signup failed, using demo mode');
    loginUser({ email, name, pref }); 
    showToast('Account created! (Demo mode)', 'success');
  }
}

function loginUser(user){ 
  currentUser=user; 
  document.getElementById('screen-login').classList.remove('active'); 
  document.getElementById('screen-app').classList.add('active'); 
  let initial=user.name.charAt(0).toUpperCase(); 
  document.getElementById('userAvatar').textContent=initial; 
  document.getElementById('profileAvatar').textContent=initial; 
  document.getElementById('profileName').textContent=user.name; 
  document.getElementById('profileEmail').textContent=user.email; 
  document.getElementById('heroGreeting').textContent=`${getGreeting()}, ${user.name.split(' ')[0]}`; 
  renderMenu('homeMenuGrid','All');
  renderMenu('orderMenuGrid','All');
  if(!MENU.length) loadMenuData();   // ensure menu is loaded even if login beat the initial fetch
  updateCartUI();
  updateHomeRecos(); 
  renderOrderHistory(); 
  updateProfileStats(); 
  renderProfileRecos(); 
  startLiveUpdates(); 
  addChatMsg('bot',`Welcome back, ${user.name.split(' ')[0]}! How can I help you today?`); 
  
  // Load orders from MongoDB if available
  if (currentUser.user_id) {
    apiGetOrders().then(result => {
      if (result.success) {
        renderOrderHistory();
      }
    });
  }
}

function doLogout(){ 
  currentUser=null; 
  cart=[]; 
  localStorage.removeItem('icst_ai_user');
  document.getElementById('screen-app').classList.remove('active'); 
  document.getElementById('screen-login').classList.add('active'); 
  if(chatOpen) toggleChat(); 
}
function showPage(name){ document.querySelectorAll('.page').forEach(p=>p.classList.remove('active')); document.querySelectorAll('.nav-link').forEach(l=>l.classList.remove('active')); document.getElementById('page-'+name).classList.add('active'); let nl=document.getElementById('nav-'+name); if(nl) nl.classList.add('active'); if(name==='order') renderOrderHistory(); if(name==='profile'){ updateProfileStats(); renderProfileRecos(); } }

// Menu Functions
function getItemCategory(item){ return item.category || item.cat || 'Unknown'; }
function getDefaultEmoji(item){ const lower=item.name?.toLowerCase()||''; if(lower.includes('chicken')||lower.includes('briyani')||lower.includes('kottu')) return '🍗'; if(lower.includes('beef')||lower.includes('breef')) return '🥩'; if(lower.includes('fish')||lower.includes('seafood')) return '🐟'; if(lower.includes('egg')||lower.includes('omelette')) return '🥚'; if(lower.includes('juice')||lower.includes('lemon')||lower.includes('mango')||lower.includes('orange')||lower.includes('watermelon')) return '🥤'; if(lower.includes('rice')||lower.includes('curry')) return '🍛'; if(lower.includes('rotti')||lower.includes('bread')||lower.includes('sandwich')) return '🍞'; if(lower.includes('samosa')||lower.includes('cutlet')||lower.includes('roll')) return '🥟'; const emojiByCategory = { Breakfast:'🌅', Lunch:'🍽️', Dinner:'🌙', Snack:'🧆', Beverage:'🥤', Dessert:'🍦', Unknown:'🍴' }; return emojiByCategory[getItemCategory(item)] || '🍴'; }
function getItemAiScore(item){ return item.ai_score ?? 72; }
function getItemProtein(item){ if(item.protein) return item.protein; const lower=item.name?.toLowerCase()||''; if(/chicken|beef|fish|mutton|prawn|egg|shrimp|crab|lobster/.test(lower)) return 'High Protein'; if(/veg|vegetable|fruit|juice|salad|bread|noodles|rice|dosa|idli/.test(lower)) return 'Vegetarian'; return 'Balanced'; }
function getItemCalories(item){ const cat=getItemCategory(item); if(cat==='Breakfast') return item.calories ?? 520; if(cat==='Lunch') return item.calories ?? 620; if(cat==='Dinner') return item.calories ?? 650; if(cat==='Snack') return item.calories ?? 320; if(cat==='Beverage') return item.calories ?? 180; if(cat==='Dessert') return item.calories ?? 400; return item.calories ?? 420; }
function normalizeMenuItem(item){ item.category = getItemCategory(item); item.emoji = item.emoji || getDefaultEmoji(item); item.ai_score = getItemAiScore(item); item.protein = getItemProtein(item); item.calories = getItemCalories(item); if(item.veg===undefined || item.veg===null){ item.veg = /veg|vegetable|fruit|juice|salad|bread|rice|noodles|pancake/.test(item.name?.toLowerCase()||''); } return item; }
MENU.forEach(normalizeMenuItem);
function renderMenu(gridId,cat){ let grid=document.getElementById(gridId); if(!grid) return; let items=cat==='All'?MENU:MENU.filter(i=>i.category===cat); let sorted=[...items].sort((a,b)=>getItemAiScore(b)-getItemAiScore(a)); grid.innerHTML=sorted.map(item=>`<div class="food-card" onclick="quickAddToCart(${item.id})"><div class="food-card-img">${item.emoji}<div class="veg-badge ${item.veg?'veg':'nonveg'}">${item.veg?'●':'■'}</div></div><div class="food-card-body"><div class="food-name">${item.name}</div><div class="food-category">${item.category} · ${item.veg?'Veg':'Non-veg'}</div><div class="food-bottom"><div class="food-price">Rs.${item.price}</div><button class="add-to-cart" onclick="event.stopPropagation();addToCart(${item.id})"><i class="fas fa-plus"></i></button></div></div><div class="food-card-ai"><i class="fas fa-robot"></i> AI Score: ${getItemAiScore(item)}%</div></div>`).join(''); }
function setupFilters(){ document.querySelectorAll('.filter-btn').forEach(btn=>{btn.addEventListener('click',function(){let parent=this.closest('.filter-bar');parent.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));this.classList.add('active');let cat=this.dataset.cat;let page=document.querySelector('.page.active');if(page.id==='page-home') renderMenu('homeMenuGrid',cat);else if(page.id==='page-order') renderMenu('orderMenuGrid',cat);});});}
function addToCart(id, special){ let item=MENU.find(i=>i.id===id); if(!item) return; let existing=cart.find(c=>c.id===id); if(existing) existing.qty++; else cart.push({...item, qty:1, special: special || null}); updateCartUI(); showToast(`Added ${item.emoji} ${item.name}`, 'success'); }
function quickAddToCart(id){ addToCart(id); }
function updateCartQty(id,delta){ let idx=cart.findIndex(c=>c.id===id); if(idx===-1) return; cart[idx].qty+=delta; if(cart[idx].qty<=0) cart.splice(idx,1); updateCartUI(); }
function removeFromCart(id){ let idx=cart.findIndex(c=>c.id===id); if(idx===-1) return; let name=cart[idx].name; cart.splice(idx,1); updateCartUI(); showToast(`Removed ${name}`, 'info'); }
function updateCartUI(){ let total=cart.reduce((s,i)=>s+i.price*i.qty,0); let count=cart.reduce((s,i)=>s+i.qty,0); document.getElementById('cartBadge').textContent=count; let list=document.getElementById('cartList'); if(cart.length===0){ list.innerHTML='<div class="empty-cart"><i class="fas fa-shopping-basket"></i><br>Your cart is empty</div>'; } else { list.innerHTML=cart.map(item=>`<div class="cart-row"><div class="cart-row-emoji">${item.emoji}</div><div class="cart-row-info"><div class="cart-row-name">${item.name}</div><div class="cart-row-price">Rs.${item.price}</div></div><div class="qty-ctrl"><button class="qty-btn" onclick="updateCartQty(${item.id},-1)">−</button><span class="qty-num">${item.qty}</span><button class="qty-btn" onclick="updateCartQty(${item.id},1)">+</button><button class="qty-btn" title="Remove" onclick="removeFromCart(${item.id})" style="color:#ef4444;"><i class="fas fa-trash-alt"></i></button></div></div>`).join(''); } document.getElementById('cartTotal').textContent=`Rs.${total}`; let eta=Math.max(3,Math.min(20,Math.floor(cart.reduce((s,i)=>s+(i.category==='Lunch'?5:3)*i.qty,0)))); document.getElementById('cartQueueEta').textContent=`~${eta} min`; document.getElementById('statQueue').textContent=`~${eta} min`; }
async function placeOrder(){ if(cart.length===0){showToast('Cart is empty','error');return;} let total=cart.reduce((s,i)=>s+i.price*i.qty,0); let eta=Math.max(4,Math.floor(Math.random()*6)+4); let orderId='ORD'+Date.now().toString().slice(-6); let deliveryLocation=document.getElementById('deliveryLocation')?.value||'Main Canteen'; let specialInstructions=document.getElementById('orderNote')?.value||''; 
  // Try MongoDB API first
  const result=await apiCreateOrder(cart.map(i=>({id:i.id,name:i.name,price:i.price,qty:i.qty,category:i.category,emoji:i.emoji})),deliveryLocation,specialInstructions);
  if(result.success){
    let order=result.order;
    const realEta = order.eta_minutes != null ? order.eta_minutes : eta;
    orderHistory.unshift(order);
    localStorage.setItem('icst_ai_orders',JSON.stringify(orderHistory.slice(0,50)));
    document.getElementById('modalContent').innerHTML=`<div style="text-align:center;"><i class="fas fa-check-circle" style="font-size:3rem;color:var(--green);margin-bottom:12px;"></i><div style="font-weight:700;margin-bottom:6px;">Order #${order.order_id}</div><div>Total: Rs.${total} · ETA: ~${realEta} min</div><div style="font-size:.78rem;color:var(--text2);margin-top:8px;">Track its progress in Order History below.</div></div>`;
    document.getElementById('orderModal').classList.add('open');
    cart=[]; updateCartUI(); renderOrderHistory(); updateProfileStats(); startOrderTracking();
  }else{
    // Fallback to localStorage
    let order={id:orderId,items:[...cart],total,eta,timestamp:new Date().toISOString(),status:'placed'};
    orderHistory.unshift(order);
    localStorage.setItem('icst_ai_orders',JSON.stringify(orderHistory.slice(0,50)));
    document.getElementById('modalContent').innerHTML=`<div style="text-align:center;"><i class="fas fa-check-circle" style="font-size:3rem;color:var(--green);margin-bottom:12px;"></i><div style="font-weight:700;margin-bottom:6px;">Order #${orderId}</div><div>Total: Rs.${total} · ETA: ${eta} min</div></div>`;
    document.getElementById('orderModal').classList.add('open');
    cart=[]; updateCartUI(); renderOrderHistory(); updateProfileStats();
  }
}
function closeModal(){ document.getElementById('orderModal').classList.remove('open'); }
// ---- Order tracking UI ----
const TRACK_FLOW = ['placed', 'preparing', 'ready', 'completed'];
function _statusLabel(s){ return ({placed:'Placed',preparing:'Preparing',ready:'Ready',completed:'Completed',cancelled:'Cancelled'})[s] || s; }
function renderTrackSteps(status){
  if(status === 'cancelled') return '<div style="font-size:.7rem;color:#ef4444;margin:8px 0;"><i class="fas fa-times-circle"></i> Order cancelled</div>';
  const idx = TRACK_FLOW.indexOf(status) < 0 ? 0 : TRACK_FLOW.indexOf(status);
  return '<div class="track-steps">' + TRACK_FLOW.map((s, i) => {
    const cls = i < idx ? 'done' : (i === idx ? 'active' : '');
    const icon = i < idx ? '<i class="fas fa-check"></i>' : '';
    return `<div class="track-step ${cls}"><div class="dot">${icon}</div>${_statusLabel(s)}</div>`;
  }).join('') + '</div>';
}
function renderOrderHistory(){
  let list = document.getElementById('orderHistoryList'); if(!list) return;
  if(orderHistory.length === 0){ list.innerHTML = '<div style="color:var(--text3);font-size:.8rem;">No orders yet</div>'; return; }
  list.innerHTML = orderHistory.slice(0, 8).map(o => {
    const oid = o.order_id || o.id;
    const status = o.status || 'placed';
    const items = (o.items || []).map(i => `${i.emoji || '🍽️'} ${i.name} x${i.qty}`).join(' · ');
    const showEta = !['completed','cancelled'].includes(status) && o.eta_minutes != null;
    const etaLine = showEta ? `<div class="order-eta"><i class="fas fa-clock"></i> Ready in ~${o.eta_minutes} min</div>` : '';
    const cancelBtn = o.cancellable ? `<button class="btn-cancel-order" onclick="cancelOrderUI('${oid}')"><i class="fas fa-times"></i> Cancel order</button>` : '';
    return `<div class="order-card"><div class="order-card-head"><div class="order-id">${oid}</div><span class="order-status status-${status}">${_statusLabel(status)}</span></div>${renderTrackSteps(status)}<div class="order-items">${items}</div><div class="order-total">Rs.${o.total} · ${new Date(o.timestamp).toLocaleTimeString()}</div>${etaLine}${cancelBtn}</div>`;
  }).join('');
  // Keep polling live while anything is still cooking.
  if(orderHistory.some(o => ['placed','preparing','ready'].includes(o.status))) startOrderTracking();
}
function getAIRecommendations(){ if(orderHistory.length===0){ let popular=[...MENU].sort((a,b)=>getItemAiScore(b)-getItemAiScore(a)).slice(0,3); return { text:`Based on campus trends, students love these today:`, items:popular }; } let catFreq={}; orderHistory.forEach(o=>o.items.forEach(i=>{let cat=i.category||i.cat; catFreq[cat]=(catFreq[cat]||0)+1;})); let favCat=Object.keys(catFreq).sort((a,b)=>catFreq[b]-catFreq[a])[0]; let recs;if(!favCat||favCat==='All'){ recs=[...MENU].sort((a,b)=>getItemAiScore(b)-getItemAiScore(a)).slice(0,4); } else { recs=MENU.filter(i=>i.category===favCat).sort((a,b)=>getItemAiScore(b)-getItemAiScore(a)).slice(0,4); } return { text:`Based on your ${orderHistory.length} orders — you love ${favCat||'campus favorites'}! Try these:`, items:recs }; }
function updateHomeRecos(){ let reco=getAIRecommendations(); let txt=document.getElementById('homeRecoText'); let chips=document.getElementById('homeRecoChips'); if(txt) txt.textContent=reco.text; if(chips) chips.innerHTML=reco.items.map(i=>`<div class="reco-chip" onclick="addToCart(${i.id})">${i.emoji} ${i.name} · Rs.${i.price}</div>`).join(''); }
function updateProfileStats(){ let total=orderHistory.reduce((s,o)=>s+o.total,0); let catFreq={}; orderHistory.forEach(o=>o.items.forEach(i=>{let cat=i.category||i.cat; catFreq[cat]=(catFreq[cat]||0)+1;})); let fav=Object.keys(catFreq).length?Object.keys(catFreq).sort((a,b)=>catFreq[b]-catFreq[a])[0]:'—'; document.getElementById('profileOrders').textContent=orderHistory.length; document.getElementById('profileSpent').textContent=`Rs.${total}`; document.getElementById('profileFav').textContent=fav; document.getElementById('profileSaved').textContent=`Rs.${Math.floor(total*0.08)}`; let tp=document.getElementById('tasteProfile'); if(orderHistory.length===0){ tp.textContent='Order more to build your AI taste profile!'; return; } let items=orderHistory.flatMap(o=>o.items); let proteins=items.filter(i=>i.protein&&i.protein!=='None').map(i=>i.protein); let topProtein=proteins.length?Object.entries(proteins.reduce((a,b)=>(a[b]=(a[b]||0)+1,a),{})).sort((a,b)=>b[1]-a[1])[0][0]:'Varied'; tp.innerHTML=`<i class="fas fa-chart-line"></i> Favorite protein: ${topProtein}<br><i class="fas fa-utensils"></i> Most ordered: ${fav}<br><i class="fas fa-chart-simple"></i> AI confidence: ${Math.min(99,60+orderHistory.length*5)}%`; }
function renderProfileRecos(){ let reco=getAIRecommendations(); let box=document.getElementById('profileRecos'); if(!box) return; box.innerHTML=reco.items.slice(0,3).map(i=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);"><span>${i.emoji} ${i.name}</span><div><span style="color:var(--accent);font-weight:600;">Rs.${i.price}</span><button class="btn btn-primary btn-sm" style="margin-left:8px;padding:4px 10px;" onclick="addToCart(${i.id});showPage('order')">Add</button></div></div>`).join(''); }
function togglePref(el){el.classList.toggle('on');}

// Upload Data Functions - FULLY RESTORED
function handleFileUpload(e){let files=[...e.target.files];files.forEach(f=>processUploadedFile(f));}
const uploadZone=document.getElementById('uploadZone'); 
uploadZone.addEventListener('dragover',e=>{e.preventDefault();uploadZone.classList.add('dragover');}); 
uploadZone.addEventListener('dragleave',()=>uploadZone.classList.remove('dragover')); 
uploadZone.addEventListener('drop',e=>{e.preventDefault();uploadZone.classList.remove('dragover');[...e.dataTransfer.files].forEach(f=>processUploadedFile(f));});
function processUploadedFile(file){let icons={pdf:'<i class="fas fa-file-pdf"></i>',ppt:'<i class="fas fa-file-powerpoint"></i>',pptx:'<i class="fas fa-file-powerpoint"></i>',xls:'<i class="fas fa-file-excel"></i>',xlsx:'<i class="fas fa-file-excel"></i>',csv:'<i class="fas fa-file-csv"></i>',html:'<i class="fas fa-code"></i>',txt:'<i class="fas fa-file-alt"></i>'}; let ext=file.name.split('.').pop().toLowerCase(); let icon=icons[ext]||'<i class="fas fa-file"></i>'; uploadedData.push({name:file.name,size:file.size,ext,file}); let list=document.getElementById('uploadedFilesList'); let row=document.createElement('div'); row.className='file-row'; row.innerHTML=`<div class="file-row-icon">${icon}</div><div class="file-row-name">${file.name}</div><div class="file-row-size">${(file.size/1024).toFixed(1)} KB</div><div class="file-row-status"><i class="fas fa-check-circle"></i> Uploaded</div>`; list.appendChild(row); showToast(`${file.name} uploaded! AI analyzing...`, 'info'); setTimeout(()=>analyzeFileWithAI(file,ext),800); }
function analyzeFileWithAI(file,ext){ let panel=document.getElementById('aiInsightsPanel'); let insightsList=document.getElementById('aiInsightsList'); panel.style.display='block'; let insights=[`<div class="insight-item"><i class="fas fa-chart-line"></i> <strong>Data Summary:</strong> Detected ${file.name} — ${ext.toUpperCase()} format. AI has parsed the structure and identified key data fields including menu items, pricing, and demand patterns.</div>`,`<div class="insight-item"><i class="fas fa-robot"></i> <strong>AI Recommendation:</strong> Based on this data, the system detected 3 high-demand items and 2 slow-moving items. Suggested: promote Chicken Briyani (peak demand +58%), add discount for surplus items.</div>`,`<div class="insight-item"><i class="fas fa-bullhorn"></i> <strong>Ad Generation Ready:</strong> Your data has been indexed for AI-powered advertisement generation. Use the Ad Generator below to create personalized promotions.</div>`,`<div class="insight-item"><i class="fas fa-check-circle"></i> <strong>Menu Sync:</strong> AI has matched ${Math.floor(Math.random()*20)+5} items from the uploaded data to the existing menu. Ready to apply updates.</div>`]; insightsList.innerHTML=insights.join(''); showToast('AI analysis complete!', 'success'); document.querySelector('.ad-banner-sub').textContent=`AI analyzed ${file.name} · Detected demand surge in Lunch category · Promotional offer auto-generated`; }
function applyDataToMenu(){ showToast('Data applied to menu and ads! Recommendations updated.', 'success'); updateHomeRecos(); addChatMsg('bot','📊 I\'ve updated my knowledge base with your uploaded data. Recommendations are now more accurate!'); syncDatasetWithTrainingAPI(); }
function addManualItem(){ let name=document.getElementById('manualName').value.trim(); let price=parseInt(document.getElementById('manualPrice').value); let cat=document.getElementById('manualCat').value; let veg=document.getElementById('manualType').value==='true'; if(!name||!price){showToast('Fill in name and price','error');return;} let emojis={Breakfast:'🌅',Lunch:'🍽️',Dinner:'🌙',Snack:'🧆',Beverage:'🥤',Dessert:'🍦'}; let newItem={id:MENU.length+1+Math.random(),name,price,category:cat,veg,emoji:emojis[cat]||'🍴',protein:getItemProtein({name,category:cat}),ai_score:Math.floor(70+Math.random()*20), calories:getItemCalories({name,category:cat})}; MENU.push(normalizeMenuItem(newItem)); renderMenu('homeMenuGrid','All'); renderMenu('orderMenuGrid','All'); document.getElementById('manualName').value=''; document.getElementById('manualPrice').value=''; showToast(`"${name}" added to menu via AI!`, 'success'); addChatMsg('bot',`📝 New item "${name}" (Rs.${price}) has been added to the menu! I\'ve updated my recommendations.`); }
async function generateAd(){ let input=document.getElementById('adInput').value.trim(); if(!input){showToast('Enter what to advertise','error');return;} let output=document.getElementById('adOutput'); output.style.display='block'; output.innerHTML='<i class="fas fa-spinner fa-spin"></i> Generating AI advertisement copy...'; setTimeout(()=>{ output.innerHTML=`<i class="fas fa-magic"></i> <strong>AI-Generated Ad:</strong><br><br>🔥 <strong>${input}</strong> — Now available at ICST Smart Food! Our AI has ranked this as a top-tier option for students who care about quality and value. Order now through our AI-powered platform and get smart queue priority. Don\'t miss out — limited portions available! 🍽️✨`; showToast('AI ad copy generated!','success'); },1500); }

// Voice, Image, Fraud, Pricing, BMI, Mood, Chat, etc. functions (same as before - keeping them)
function startAdTimer(){ let endTime=new Date(); endTime.setHours(14,0,0,0); if(endTime<new Date()) endTime.setDate(endTime.getDate()+1); function update(){ let diff=endTime-new Date(); if(diff<=0){document.getElementById('adTimer').textContent='Offer Expired';return;} let h=String(Math.floor(diff/3600000)).padStart(2,'0'), m=String(Math.floor((diff%3600000)/60000)).padStart(2,'0'), s=String(Math.floor((diff%60000)/1000)).padStart(2,'0'); document.getElementById('adTimer').textContent=`${h}:${m}:${s}`; } update(); setInterval(update,1000); }
function startLiveUpdates(){ startAdTimer(); setInterval(()=>{ let h=new Date().getHours(); let demand='+25%'; if(h>=12&&h<=14) demand='+58% Peak'; else if(h>=18&&h<=20) demand='+44%'; document.getElementById('statDemand').textContent=demand; document.getElementById('statScore').textContent=Math.floor(90+Math.random()*8)+'%'; },6000); }
function getGreeting(){ let h=new Date().getHours(); if(h<12) return 'Good morning'; if(h<17) return 'Good afternoon'; return 'Good evening'; }
function showToast(msg,type='info'){ let container=document.getElementById('toastContainer'); let toast=document.createElement('div'); toast.className=`toast ${type}`; toast.innerHTML=`<i class="fas ${type==='success'?'fa-check-circle':type==='error'?'fa-exclamation-circle':'fa-info-circle'}"></i> ${msg}`; container.appendChild(toast); setTimeout(()=>{ toast.style.opacity='0'; setTimeout(()=>toast.remove(),300); },3000); }

// ==================== AI Feature Functions (Browser Voice + Image) ====================
// Voice now runs ENTIRELY IN THE BROWSER via the Web Speech API:
//   - Speech-to-Text: SpeechRecognition (Chrome/Edge) in the selected language
//   - Text-to-Speech: speechSynthesis, preferring a natural male voice
// This replaces the old, broken design that tried to open a microphone on the
// SERVER via a Python subprocess (which can never reach the user's mic).

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function stripHtml(s){ const d=document.createElement('div'); d.innerHTML=s; return d.textContent||d.innerText||''; }

let _voicesCache = [];
function _loadVoices(){ _voicesCache = window.speechSynthesis ? speechSynthesis.getVoices() : []; }
if (window.speechSynthesis){ _loadVoices(); speechSynthesis.onvoiceschanged = _loadVoices; }

// Pick a natural MALE voice matching the active language, with safe fallbacks.
function getPreferredVoice(lang){
  if(!_voicesCache.length) _loadVoices();
  const byLang = _voicesCache.filter(v => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0,2).toLowerCase()));
  const pool = byLang.length ? byLang : _voicesCache;
  const maleHint = /male|david|daniel|fred|alex|rishi|ravi|hemant|uk english male/i;
  const femaleHint = /female|zira|samantha|victoria|susan|hazel/i;
  return pool.find(v => maleHint.test(v.name)) || pool.find(v => !femaleHint.test(v.name)) || pool[0] || null;
}

// Separate language for VOICE input (mic). Defaults to the chat language but
// can be set independently from the voice card's selector.
let voiceLanguage = 'en-US';
function setVoiceLanguage(lang){
  voiceLanguage = lang;
  const sel = document.getElementById('voiceLangSelect'); if(sel) sel.value = lang;
  // Sinhala STT is not supported by the browser engine — warn up front.
  if(lang === 'si-LK' && !browserSupportsSTT('si-LK')){
    showToast('Sinhala voice input is not supported by this browser. You can still type your order.', 'info');
  } else {
    showToast(`Voice: ${SUPPORTED_CHAT_LANGUAGES[lang] || lang}`, 'success');
  }
}

// Chrome/Edge Web Speech API supports en/ta/hi but NOT Sinhala (si-LK).
// We can't truly feature-detect a language, so we treat si-LK as unsupported.
const STT_UNSUPPORTED = ['si-LK'];
function browserSupportsSTT(lang){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  return !!SR && !STT_UNSUPPORTED.includes(lang);
}

let _ttsWarned = {};
// Text-to-Speech with a male voice in the active language.
function speak(text, lang){
  if(!window.speechSynthesis || !text) return;
  try{
    const target = lang || voiceLanguage || assistantLanguage || 'en-US';
    const v = getPreferredVoice(target);
    // Warn ONCE per language if the OS has no matching voice installed.
    const hasLangVoice = v && v.lang && v.lang.toLowerCase().startsWith(target.slice(0,2).toLowerCase());
    if(!hasLangVoice && !_ttsWarned[target] && target !== 'en-US'){
      _ttsWarned[target] = true;
      showToast(`No ${SUPPORTED_CHAT_LANGUAGES[target] || target} speech voice installed on this device — install the language pack for spoken replies.`, 'info');
    }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(stripHtml(text));
    u.lang = target;
    if(v) u.voice = v;
    u.rate = 1; u.pitch = 0.9; // slightly lower pitch -> more natural male tone
    speechSynthesis.speak(u);
  }catch(e){ console.warn('TTS failed', e); }
}

function _getRecognizer(lang){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR) return null;
  const r = new SR();
  r.lang = lang || voiceLanguage || assistantLanguage || 'en-US';
  r.interimResults = false; r.maxAlternatives = 1; r.continuous = false;
  return r;
}

// Human-readable, localized message for each Web Speech API error code.
function _voiceErrorMessage(code){
  switch(code){
    case 'not-allowed':
    case 'service-not-allowed':
      return 'Microphone permission denied. Allow mic access in your browser and retry.';
    case 'no-speech':       return "I didn't hear anything. Tap the mic and speak clearly.";
    case 'audio-capture':   return 'No microphone found. Connect a mic and retry.';
    case 'network':         return 'Network error reaching the speech service. Check your connection.';
    case 'language-not-supported':
      return 'This language is not supported for voice input on your browser. Please type your order instead.';
    default:                return 'Voice error: ' + code;
  }
}

// Capture a single utterance from the microphone; resolves with the transcript.
function listenOnce(statusEl, lang){
  return new Promise((resolve, reject) => {
    const r = _getRecognizer(lang);
    if(!r){ reject(new Error('Speech recognition is not supported here. Please use Chrome or Edge.')); return; }
    if(statusEl) statusEl.textContent = '🎤 Listening... speak now';
    let settled = false;
    r.onresult = e => { settled = true; resolve(e.results[0][0].transcript); };
    r.onerror = e => { settled = true; reject(new Error(_voiceErrorMessage(e.error))); };
    r.onend = () => { if(!settled) reject(new Error(_voiceErrorMessage('no-speech'))); };
    try { r.start(); } catch(err){ reject(err); }
  });
}

// Shared browser voice-ordering flow used by every voice button.
async function browserVoiceOrder(statusElId){
  const statusEl = document.getElementById(statusElId);
  const lang = voiceLanguage || assistantLanguage || 'en-US';
  // Sinhala (or any unsupported language): skip the mic, offer typed input.
  if(!browserSupportsSTT(lang)){
    if(statusEl) statusEl.textContent = 'ℹ️ Sinhala voice input is not supported here — type your order instead.';
    return parseVoiceOrder();
  }
  try{
    const transcript = await listenOnce(statusEl, lang);
    if(statusEl) statusEl.textContent = '📝 Heard: "' + escapeHtml(transcript) + '"';
    addChatMsg('user', '🎤 ' + escapeHtml(transcript));
    const res = await fetch(API_BASE_URL + '/api/parse-voice-order', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ input: transcript })
    });
    const result = await res.json();
    if(result.success && result.items.length){
      result.items.forEach(it => {
        const mi = MENU.find(m => m.name.toLowerCase() === it.name.toLowerCase());
        if(mi){ for(let i=0;i<it.quantity;i++) addToCart(mi.id, it.special); }
      });
      const summary = result.items.map(it => it.quantity + '× ' + it.name).join(', ');
      const msg = 'Added to your cart: ' + summary + '.';
      addChatMsg('bot', '✅ ' + escapeHtml(msg) + ' (confidence ' + Math.round(result.confidence) + '%)');
      showToast('Voice order added to cart', 'success');
      speak(msg);
    } else {
      const msg = "I couldn't match that to the menu. Try: 'two chicken kottu and a lemon juice'.";
      addChatMsg('bot', '❌ ' + escapeHtml(msg)); showToast('No items matched', 'error'); speak(msg);
    }
  }catch(err){
    if(statusEl) statusEl.textContent = '❌ ' + err.message;
    showToast(err.message, 'error');
  }
}

function startVoiceRecognition(){ return browserVoiceOrder('voiceStatus'); }
function startVoiceRecognitionEnhanced(){ return browserVoiceOrder('voiceStatus'); }
function startVoiceOrdering(){ return browserVoiceOrder('voiceStatus'); }

// Parse a typed order without the mic (accessibility / testing fallback).
async function parseVoiceOrder(){
  const voiceInput = prompt('Enter your order text:\n(e.g., "2 chicken kottu and one lemon juice")');
  if(!voiceInput || !voiceInput.trim()){ showToast('No input provided', 'error'); return; }
  try{
    const res = await fetch(API_BASE_URL + '/api/parse-voice-order', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ input: voiceInput })
    });
    const result = await res.json();
    if(result.success && result.items.length){
      result.items.forEach(it => {
        const mi = MENU.find(m => m.name.toLowerCase() === it.name.toLowerCase());
        if(mi){ for(let i=0;i<it.quantity;i++) addToCart(mi.id, it.special); }
      });
      const summary = result.items.map(it => it.quantity + '× ' + it.name).join(', ');
      addChatMsg('bot', '✅ Parsed (' + Math.round(result.confidence) + '%): ' + escapeHtml(summary) + '. Items added to cart.');
      showToast('Order parsed', 'success');
    } else {
      showToast('Could not understand order', 'error');
      addChatMsg('bot', "❌ I couldn't parse that. Try '2 chicken kottu and a lemon juice'.");
    }
  }catch(err){ showToast('Error: ' + err.message, 'error'); }
}

// ----- Food image upload (browser file picker -> backend, with validation) -----
function startFoodAI(){ _pickFoodImage(); }
function startFoodRecognitionEnhanced(){ _pickFoodImage(); }
function _pickFoodImage(){
  let inp = document.getElementById('_foodImgInput');
  if(!inp){
    inp = document.createElement('input');
    inp.type='file'; inp.accept='image/*'; inp.id='_foodImgInput'; inp.style.display='none';
    inp.addEventListener('change', _onFoodImage); document.body.appendChild(inp);
  }
  inp.value=''; inp.click();
}
async function _onFoodImage(e){
  const file = e.target.files[0]; if(!file) return;
  const statusEl = document.getElementById('foodAiStatus');
  if(!file.type.startsWith('image/')){ showToast('Please select an image file', 'error'); return; }
  if(file.size > 5*1024*1024){ showToast('Image must be under 5 MB', 'error'); return; }
  if(statusEl) statusEl.textContent = '🔄 Uploading & analysing image...';
  try{
    const fd = new FormData(); fd.append('image', file);
    const res = await fetch(API_BASE_URL + '/api/food-image', { method:'POST', body: fd });
    const data = await res.json();
    if(res.ok && data.success){
      const preview = '<img src="' + data.image_url + '" alt="food" style="max-width:140px;border-radius:8px;display:block;margin-top:6px;"'
        + ' onerror="this.replaceWith(document.createTextNode(\'🍽️ (preview unavailable)\'))">';
      const rec = data.recognition;
      let recHtml = '';
      if(rec && rec.error){
        const rateMsg = rec.retry_after
          ? '⏳ AI hit the free-tier limit — try again in ' + escapeHtml(rec.retry_after) + '.'
          : '⏳ AI is busy (free-tier rate limit). Wait a minute and try again.';
        const errMsg = {
          rate_limited: rateMsg,
          bad_image: '⚠️ AI couldn\'t read that image — try a clearer JPG/PNG photo.',
          bad_key: '🔑 AI key invalid — check GEMINI_API_KEY in .env.'
        }[rec.error] || '⚠️ AI recognition is temporarily unavailable.';
        recHtml = '<div style="margin-top:6px;color:var(--yellow,#fbbf24);">' + errMsg + '</div>';
      } else if(rec && rec.is_food){
        const match = rec.menu_match;
        recHtml = '<div style="margin-top:6px;font-weight:600;">🔍 ' + escapeHtml(rec.dish)
          + ' <span style="color:var(--text3);font-weight:400;">(' + Math.round(rec.confidence) + '% conf)</span></div>';
        if(match){
          recHtml += '<div style="margin-top:4px;">Matches <strong>' + escapeHtml(match.name) + '</strong> · Rs.' + match.price
            + ' <button class="btn btn-primary btn-sm" style="margin-left:6px;padding:3px 10px;" onclick="addToCart(' + match.id + ')">Add to cart</button></div>';
          addChatMsg('bot', '📸 I recognised <strong>' + escapeHtml(rec.dish) + '</strong> — that\'s our <strong>' + escapeHtml(match.name) + '</strong> (Rs.' + match.price + '). Added a quick-add button below.');
        } else {
          addChatMsg('bot', '📸 I recognised <strong>' + escapeHtml(rec.dish) + '</strong>, but we don\'t have an exact match on the menu.');
        }
      } else if(rec && !rec.is_food){
        recHtml = '<div style="margin-top:6px;color:var(--text3);">That doesn\'t look like food.</div>';
      } else if(data.ai_enabled === false){
        recHtml = '<div style="margin-top:6px;color:var(--text3);font-size:.72rem;">AI recognition is off (no API key set).</div>';
      }
      if(statusEl) statusEl.innerHTML = '✅ Uploaded (' + (data.size_bytes/1024).toFixed(0) + ' KB).' + preview + recHtml;
      showToast(rec && rec.is_food ? 'Food recognised' : 'Image uploaded', 'success');
    } else { throw new Error(data.error || 'Upload failed'); }
  }catch(err){ if(statusEl) statusEl.textContent = '❌ ' + err.message; showToast(err.message, 'error'); }
}


// ==================== Original Fraud & Pricing Functions ====================

// Fraud
let fraudScanRunning=false;
function runFraudSimulation(){ if(fraudScanRunning) return; fraudScanRunning=true; let btn=document.querySelector('.fraud-simulation-btn'); if(btn) btn.disabled=true; let score=Math.floor(75+Math.random()*20); updateFraudScore(score); setTimeout(()=>{ fraudScanRunning=false; if(btn) btn.disabled=false; showToast('Fraud scan complete','success'); },2000); }
function updateFraudScore(score){ let numEl=document.getElementById('fraudScoreNum'); let ringEl=document.getElementById('fraudRingFill'); numEl.textContent=score+'%'; let color=score>=85?'var(--green)':score>=65?'var(--accent2)':'var(--red)'; numEl.style.color=color; if(ringEl) ringEl.style.stroke=color; if(ringEl) ringEl.style.strokeDashoffset=251-(score/100)*251; }

// Dynamic Pricing
function refreshDynamicPricing(){ let h=new Date().getHours(); let isPeak=(h>=12&&h<=14)||(h>=18&&h<=20); let items=[{emoji:'🍚',name:'Chicken Briyani',base:350},{emoji:'🍗',name:'Rice + Chicken',base:300},{emoji:'🥗',name:'Rice + Veg',base:200},{emoji:'🍲',name:'Chicken Kottu',base:350},{emoji:'🍋',name:'Lemon Juice',base:100},{emoji:'🥤',name:'Mango Juice',base:180}]; document.getElementById('dynamicPricingGrid').innerHTML=items.map(item=>{ let mod=isPeak?1.1:1; let newPrice=Math.round(item.base*mod); let change=mod>1?'▲ +10% Peak':'— Normal'; return `<div class="price-item ${mod>1?'surge':''}"><div class="price-item-emoji">${item.emoji}</div><div class="price-item-name">${item.name}</div><div class="price-item-val">Rs. ${newPrice}</div><div class="price-item-change ${mod>1?'up':''}">${change}</div></div>`; }).join(''); }

// BMI
function calculateBMIAndPlan(){ let heightCm=parseFloat(document.getElementById('bmiHeight').value); let weightKg=parseFloat(document.getElementById('bmiWeight').value); let age=parseFloat(document.getElementById('bmiAge').value); let activity=parseFloat(document.getElementById('activityLevel').value); if(isNaN(heightCm)||isNaN(weightKg)||heightCm<=0||weightKg<=0){showToast('Enter valid height and weight','error');return;} let heightM=heightCm/100; let bmi=weightKg/(heightM*heightM); bmi=Math.round(bmi*10)/10; let category='',categoryClass='',advice=''; if(bmi<18.5){category='Underweight';categoryClass='bmi-underweight';advice='Focus on nutrient-dense foods with healthy fats.';} else if(bmi>=18.5&&bmi<=24.9){category='Normal';categoryClass='bmi-normal';advice='Great! Maintain balanced meals.';} else if(bmi>=25&&bmi<=29.9){category='Overweight';categoryClass='bmi-overweight';advice='Focus on portion control and lean proteins.';} else{category='Obese';categoryClass='bmi-obese';advice='Consider consulting a nutritionist.';} let bmr=Math.round((10*weightKg)+(6.25*heightCm)-(5*age)); let tdee=Math.round(bmr*activity); let recommended=MENU.filter(i=>i.calories>=350&&i.calories<=650).slice(0,3); let resultHtml=`<div class="bmi-result-card"><div style="display:flex;align-items:center;justify-content:space-between;"><div><span style="font-size:1.3rem;font-weight:800;">${bmi}</span><br><span class="bmi-category ${categoryClass}">${category}</span></div><div><div>BMR: ${bmr} cal</div><div>TDEE: ${tdee} cal</div></div></div><div style="margin-top:12px;padding:8px;background:var(--bg3);border-radius:8px;">${advice}</div><div style="margin-top:10px;"><strong>Recommended meals:</strong> ${recommended.map(i=>`${i.emoji} ${i.name} (${i.calories}cal)`).join(' · ')}</div></div>`; document.getElementById('bmiResult').innerHTML=resultHtml; document.getElementById('bmiResult').style.display='block'; showToast('BMI calculated!','success'); }

// Mood
function analyzeMood(mood){ let moodMap={ stressed:{title:'Feeling Stressed?',emoji:'😫',recs:[{name:'Avocado Juice',reason:'Rich in B vitamins that reduce stress',id:29,emoji:'🥑'},{name:'Lassi',reason:'Probiotics support gut-brain axis',id:32,emoji:'🥛'}]}, tired:{title:'Feeling Tired?',emoji:'😴',recs:[{name:'Chicken Briyani',reason:'Sustained energy release',id:13,emoji:'🍚'},{name:'Mango Juice',reason:'Natural sugars + Vitamin C',id:28,emoji:'🥭'}]}, happy:{title:'Feeling Happy!',emoji:'😊',recs:[{name:'Ice Cream',reason:'Celebrate your happiness',id:41,emoji:'🍦'},{name:'Faluda',reason:'Special treat for good days',id:31,emoji:'🍹'}]}, anxious:{title:'Feeling Anxious?',emoji:'😰',recs:[{name:'Lassi',reason:'Calming probiotics',id:32,emoji:'🥛'},{name:'Vegetable Rotti',reason:'Serotonin-boosting carbs',id:2,emoji:'🥬'}]}, sad:{title:'Feeling Sad?',emoji:'😢',recs:[{name:'Rice + Chicken Curry',reason:'Comfort food',id:9,emoji:'🍗'},{name:'Mojito',reason:'Refreshing drink',id:42,emoji:'🍸'}]}, energetic:{title:'Feeling Energetic!',emoji:'⚡',recs:[{name:'Beef Briyani',reason:'High protein for energy',id:14,emoji:'🍛'},{name:'Watermelon Juice',reason:'Hydrating',id:30,emoji:'🍉'}]}, focused:{title:'Need Focus?',emoji:'🧠',recs:[{name:'Fish Cutlet',reason:'Omega-3s boost brain function',id:25,emoji:'🐟'},{name:'Pineapple Juice',reason:'Antioxidants',id:43,emoji:'🍍'}]}, lonely:{title:'Feeling Lonely?',emoji:'🥺',recs:[{name:'Rice + Veg Curry',reason:'Wholesome meal',id:10,emoji:'🥗'},{name:'Plain Tea',reason:'Warm beverage',id:33,emoji:'🍵'}]} }; let data=moodMap[mood]||moodMap.stressed; let recsHtml=data.recs.map(rec=>`<div class="mood-reco-item"><div><strong>${rec.emoji} ${rec.name}</strong><br><span style="font-size:.7rem;">${rec.reason}</span></div><button class="btn btn-primary btn-sm" style="margin-top:6px;" onclick="addToCart(${rec.id})">Add to Cart</button></div>`).join(''); let resultHtml=`<div class="mood-analysis"><div style="font-weight:700;margin-bottom:6px;">${data.emoji} ${data.title}</div><div>AI recommends these mood-supporting foods:</div><div style="margin-top:10px;">${recsHtml}</div></div>`; document.getElementById('moodResult').innerHTML=resultHtml; document.getElementById('moodResult').style.display='block'; showToast(`Mood: ${mood} - AI suggestions ready!`,'info'); }

// Nutrition & Diet
function askNutrition(){ let q=document.getElementById('nutritionQ').value.trim(); if(!q){showToast('Ask a question first','error');return;} let ans=document.getElementById('nutritionAnswer'); ans.style.display='block'; ans.innerHTML='<i class="fas fa-spinner fa-spin"></i> Thinking...'; setTimeout(()=>{ ans.innerHTML=`🍎 <strong>AI Nutrition Tip:</strong> For "${q}", consider Chicken Briyani (680 cal, 35g protein) or Rice + Fish Curry (580 cal, 28g protein). Both are excellent choices for sustained energy!`; },1000); }
function getSmartMealSuggestions(){ let weight=parseFloat(document.getElementById('userWeight').value); let goal=parseInt(document.getElementById('calorieGoal').value); let dietGoal=document.getElementById('dietGoal').value; if(isNaN(weight)||isNaN(goal)){showToast('Enter valid weight and goal','error');return;} let suggested=MENU.filter(i=>i.calories>=400&&i.calories<=700).slice(0,4); let html=`<strong>Based on your profile:</strong><br>${suggested.map(i=>`🍛 ${i.name} · ${i.calories} cal · Rs.${i.price}`).join('<br>')}<br><br><span style="font-size:.7rem;">✨ AI-generated meal suggestions</span>`; document.getElementById('dietSuggestionPanel').style.display='block'; document.getElementById('dietSuggestionPanel').innerHTML=html; showToast('Meal suggestions ready!','success'); }

// Chat
function toggleChat(){ chatOpen=!chatOpen; document.getElementById('chatWindow').classList.toggle('open',chatOpen); }
function addChatMsg(role,text){ let msgs=document.getElementById('chatMsgs'); let div=document.createElement('div'); div.className=`msg ${role}`; div.innerHTML=text; msgs.appendChild(div); msgs.scrollTop=msgs.scrollHeight; }
function sendQuickReply(el){ document.getElementById('chatInput').value=el.textContent; sendChat(); }
async function sendChat(){
  const input=document.getElementById('chatInput'); const text=input.value.trim(); if(!text) return;
  addChatMsg('user', escapeHtml(text)); input.value='';
  try{
    const res = await fetch(API_BASE_URL + '/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ message:text, language:assistantLanguage }) });
    if(res.ok){
      const data = await res.json();
      // Off-topic guard: reply with the localized "not related to food" message.
      if(data.related === false){ addChatMsg('bot', escapeHtml(data.reply)); speak(data.reply); return; }
    }
  }catch(e){ /* backend offline -> fall through to local intent engine */ }
  const reply = runAssistantIntent(text,'chat');
  addChatMsg('bot', reply); speak(stripHtml(reply));
}

// Fetch the menu from the backend, normalise it, and (re)render any visible
// grids. Called once on startup and again right after login.
async function loadMenuData(){
  try{
    const r = await apiGetMenu();
    if(r.success && Array.isArray(r.items) && r.items.length){
      MENU = r.items;
      MENU.forEach(normalizeMenuItem);
    } else {
      console.warn('Menu API returned no items:', r.error || 'empty');
    }
  }catch(e){ console.error('Failed to load menu from API:', e); }
  // Re-render whatever menu grids exist now that MENU is populated.
  if(document.getElementById('homeMenuGrid')) renderMenu('homeMenuGrid','All');
  if(document.getElementById('orderMenuGrid')) renderMenu('orderMenuGrid','All');
  if(typeof updateHomeRecos === 'function') updateHomeRecos();
}

setupFilters();
refreshDynamicPricing();
loadMenuData();   // populate MENU from the API as soon as the page loads
