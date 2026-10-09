const SUBSCRIPTION_TOPICS={news:'World & AI news',markets:'Global markets',health:'Healthy living',recipes:'Family kitchen',english:'Everyday English'};
function subscriptionSection(route){
 const ready=Boolean(window.REAL_FAMILY_SUBSCRIPTIONS?.endpoint);
 return `<section class="subscription-panel" aria-labelledby="subscription-heading"><div><p class="eyebrow">GOOD THINGS, IN YOUR INBOX</p><h2 id="subscription-heading">Stay connected.</h2><p>A daily email with the topics you choose. News and market pages refresh every three hours; your inbox receives one daily digest, scheduled for 7:30 AM PT.</p></div><form id="subscription-form"><label class="subscription-email">Email address<input name="email" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com" required></label><fieldset><legend>What would you like to receive?</legend><div class="subscription-topics">${Object.entries(SUBSCRIPTION_TOPICS).map(([key,label])=>`<label><input type="checkbox" name="topics" value="${key}" ${key===route?'checked':''}> ${label}</label>`).join('')}</div></fieldset><label class="subscription-consent"><input type="checkbox" name="consent" required><span><strong>I agree to receive my selected emails.</strong><small>I can unsubscribe at any time.</small></span></label><div class="subscription-trap" hidden aria-hidden="true"><input name="website" aria-label="Leave this empty" tabindex="-1" autocomplete="off"></div><div class="subscription-actions"><button class="button" type="submit" ${ready?'':'disabled'}>Subscribe by email <span>↗</span></button><p class="fine" id="subscription-status" role="status" aria-live="polite">${ready?'Confirm your email to start. Confirmation emails are processed hourly; delivery may be delayed.':'Email subscriptions are being connected. Please check back soon.'}</p></div><p class="fine subscription-privacy">Your email is used for subscription messages only. Each digest includes an unsubscribe link.</p></form></section>`;
}
document.addEventListener('submit',async event=>{
 const form=event.target;if(form.id!=='subscription-form')return;event.preventDefault();
 const status=form.querySelector('#subscription-status'),button=form.querySelector('button[type="submit"]'),fields=new FormData(form),topics=fields.getAll('topics');
 if(!topics.length){status.textContent='Choose at least one topic.';return}
 if(!form.reportValidity())return;
 const endpoint=window.REAL_FAMILY_SUBSCRIPTIONS?.endpoint;
 if(!endpoint){status.textContent='Email subscriptions are not available yet.';return}
 button.disabled=true;form.dataset.submitting='true';status.textContent='Requesting your confirmation email…';
 try{
  const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:fields.get('email'),topics,consent:fields.get('consent')==='on',website:fields.get('website')})});
  if(!response.ok)throw Error(response.status===429?'Please wait before requesting another confirmation.':'Your request could not be saved. Please try again.');
  (document.querySelector('#subscription-status')||status).textContent='Request received. Your confirmation email is queued. Messages are processed hourly; delivery may be delayed. Check your inbox and spam folder. Your subscription starts only after confirmation.';
 }catch(error){(document.querySelector('#subscription-status')||status).textContent=error.message==='Failed to fetch'?'We could not connect. Please try again shortly.':error.message}
 finally{const active=document.querySelector('#subscription-form');if(active){active.dataset.submitting='false';active.querySelector('button[type=submit]').disabled=false}}
});

function captureSubscriptionDraft(){
 const form=document.querySelector('#subscription-form');if(!form)return null;
 return {route:document.querySelector('main').dataset.route,email:form.elements.email.value,topics:[...form.querySelectorAll('[name=topics]:checked')].map(e=>e.value),consent:form.elements.consent.checked,focused:form.contains(document.activeElement)?document.activeElement.name:null,submitting:form.dataset.submitting==='true',status:form.querySelector('#subscription-status').textContent};
}
function restoreSubscriptionDraft(draft,route){
 if(!draft||draft.route!==route)return;
 const form=document.querySelector('#subscription-form');if(!form)return;
 form.elements.email.value=draft.email;form.elements.consent.checked=draft.consent;
 form.querySelectorAll('[name=topics]').forEach(input=>{input.checked=draft.topics.includes(input.value)});
 form.dataset.submitting=String(draft.submitting);if(draft.submitting)form.querySelector('button[type=submit]').disabled=true;
 form.querySelector('#subscription-status').textContent=draft.status;
 if(draft.focused){const control=form.querySelector('[name="'+draft.focused+'"]');if(control)control.focus({preventScroll:true})}
}
