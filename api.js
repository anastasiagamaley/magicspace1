// MagicSpace – centrálne API volania
const API = {
  async getSessions(project="main"){ const r=await fetch(`/api/sessions?project=${project}`); return r.json(); },
  async createSession(data){ const r=await fetch("/api/sessions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); return r.json(); },
  async updateSession(id,data){ const r=await fetch(`/api/sessions/${id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); return r.json(); },
  async deleteSession(id){ const r=await fetch(`/api/sessions/${id}`,{method:"DELETE"}); return r.json(); },
  async cancelSession(id){ const r=await fetch(`/api/sessions/${id}/cancel`,{method:"POST"}); return r.json(); },

  async getBookings(){ const r=await fetch("/api/bookings"); return r.json(); },
  async createBooking(data){
    const r=await fetch("/api/bookings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba rezervácie");}
    return r.json();
  },
  async confirmBooking(id){ const r=await fetch(`/api/bookings/${id}/confirm`,{method:"POST"}); return r.json(); },
  async deleteBooking(id){ const r=await fetch(`/api/bookings/${id}`,{method:"DELETE"}); return r.json(); },

  async getContacts(){ const r=await fetch("/api/contacts"); return r.json(); },
  async createContact(data){
    const r=await fetch("/api/contacts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba odoslania");}
    return r.json();
  },
  async deleteContact(id){ const r=await fetch(`/api/contacts/${id}`,{method:"DELETE"}); return r.json(); },
  async markContactRead(id){ const r=await fetch(`/api/contacts/${id}/read`,{method:"POST"}); return r.json(); },

  async getStats(){ const r=await fetch("/api/stats"); return r.json(); },

  async uploadImage(file){
    const fd=new FormData(); fd.append("file",file);
    const r=await fetch("/api/upload",{method:"POST",body:fd});
    if(!r.ok){const e=await r.json();throw new Error(e.error||"Chyba uploadu");}
    return r.json(); // {url: "/uploads/img_xxx.jpg"}
  },

  async checkAuth(password){
    const r=await fetch("/api/auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password})});
    return r.ok;
  }
};
