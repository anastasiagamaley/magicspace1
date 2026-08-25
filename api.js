// MagicSpace – centrálne API volania
const API = {
  // Nastavte na funkciu, ktorá zobrazí prihlásenie (admin.html to robí).
  onUnauthorized: null,

  // Všetky volania idú cez tento wrapper – session cookie sa posiela
  // automaticky a vypršané prihlásenie sa zachytí na jednom mieste.
  async _fetch(url, opts){
    const r = await fetch(url, Object.assign({credentials:"same-origin"}, opts||{}));
    if(r.status === 401 && typeof API.onUnauthorized === "function") API.onUnauthorized();
    return r;
  },

  async getSessions(project="main", opts={}){
    let url=`/api/sessions?project=${project}`;
    if(opts.upcoming) url+=`&upcoming=${opts.upcoming}`;
    const r=await API._fetch(url); return r.json();
  },
  async createSession(data){ const r=await API._fetch("/api/sessions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); return r.json(); },
  async updateSession(id,data){ const r=await API._fetch(`/api/sessions/${id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); return r.json(); },
  async deleteSession(id){ const r=await API._fetch(`/api/sessions/${id}`,{method:"DELETE"}); return r.json(); },
  async deleteRecurGroup(id){ const r=await API._fetch(`/api/sessions/${id}/recur-group`,{method:"DELETE"}); return r.json(); },
  async cancelSession(id){ const r=await API._fetch(`/api/sessions/${id}/cancel`,{method:"POST"}); return r.json(); },

  async getBookings(){ const r=await API._fetch("/api/bookings"); return r.json(); },
  async createBooking(data){
    const r=await API._fetch("/api/bookings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba rezervácie");}
    return r.json();
  },
  async confirmBooking(id){ const r=await API._fetch(`/api/bookings/${id}/confirm`,{method:"POST"}); return r.json(); },
  async deleteBooking(id){ const r=await API._fetch(`/api/bookings/${id}`,{method:"DELETE"}); return r.json(); },

  async getContacts(){ const r=await API._fetch("/api/contacts"); return r.json(); },
  async createContact(data){
    const r=await API._fetch("/api/contacts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba odoslania");}
    return r.json();
  },
  async deleteContact(id){ const r=await API._fetch(`/api/contacts/${id}`,{method:"DELETE"}); return r.json(); },
  async markContactRead(id){ const r=await API._fetch(`/api/contacts/${id}/read`,{method:"POST"}); return r.json(); },

  async getStats(){ const r=await API._fetch("/api/stats"); return r.json(); },

  async uploadImage(file){
    const fd=new FormData(); fd.append("file",file);
    const r=await API._fetch("/api/upload",{method:"POST",body:fd});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba uploadu");}
    return r.json(); // {url: "/uploads/img_xxx.jpg"}
  },

  async getReviews(page){ const r=await API._fetch(`/api/reviews?page=${page}`); return r.json(); },
  async getReviewsAdmin(){ const r=await API._fetch("/api/reviews/admin"); return r.json(); },
  async createReview(data){ const r=await API._fetch("/api/reviews",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); return r.json(); },
  async approveReview(id){ const r=await API._fetch(`/api/reviews/${id}/approve`,{method:"POST"}); return r.json(); },
  async deleteReview(id){ const r=await API._fetch(`/api/reviews/${id}`,{method:"DELETE"}); return r.json(); },

  async getClients(){ const r=await API._fetch("/api/clients"); return r.json(); },
  async sendClientEmail(data){
    const r=await API._fetch("/api/clients/send-email",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba odoslania");}
    return r.json();
  },

  async checkAuth(password){
    const r=await fetch("/api/auth",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({password})});
    return r.ok;
  },
  async checkSession(){
    try{ const r=await fetch("/api/auth/check",{credentials:"same-origin"}); return (await r.json()).ok===true; }
    catch(e){ return false; }
  },
  async logoutServer(){
    try{ await fetch("/api/auth/logout",{method:"POST",credentials:"same-origin"}); }catch(e){}
  }
};
