const SUBSCRIPTION_TOPICS={news:'World & AI news',markets:'Global markets',health:'Healthy living',recipes:'Family kitchen',english:'Everyday English'};
function subscriptionSection(route){
 const ready=Boolean(window.REAL_FAMILY_SUBSCRIPTIONS?.endpoint);
 return `<section class="subscription-panel" aria-labelledby="subscription-heading"><div><p class="eyebrow">GOOD THINGS, IN YOUR INBOX</p><h2 id="subscription-heading">Stay connected.</h2><p>A daily email with the topics you choose. News and market pages refresh every three hours; your inbox receives one daily digest.</p></div><form id="subscription-form"><label class="subscription-email">Email address<input name="email" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com" required></label><fieldset><legend>What would you like to receive?</legend><div class="subscription-topics">${Object.entries(SUBSCRIPTION_TOPICS).map(([key,label])=>`<label><input type="checkbox" name="topics" value="${key}" ${key===route?'checked':''}> ${label}</label>`).join('')}</div></fieldset><label class="subscription-consent"><input type="checkbox" name="consent" required><span><strong>I agree to receive my selected emails.</strong><small>I can unsubscribe at any time.</small></span></label><div class="subscription-trap" hidden aria-hidden="true"><input name="website" aria-label="Leave this empty" tabindex="-1" autocomplete="off"></div><div class="subscription-actions"><button class="button" type="submit" ${ready?'':'disabled'}>Subscribe by email <span>↗</span></button><p class="fine" id="subscription-status" role="status" aria-live="polite">${ready?'Confirm your email to start. Confirmation messages are processed within the next hour.':'Email subscriptions are being connected. Please check back soon.'}</p></div><p class="fine subscription-privacy">Your email is used for subscription messages only. Each digest includes an unsubscribe link.</p></form></section>`;
}
document.addEventListener('submit',async event=>{
 const form=event.target;if(form.id!=='subscription-form')return;event.preventDefault();
 const status=form.querySelector('#subscription-status'),button=form.querySelector('button[type="submit"]'),fields=new FormData(form),topics=fields.getAll('topics');
 if(!topics.length){status.textContent='Choose at least one topic.';return}
 if(!form.reportValidity())return;
 const endpoint=window.REAL_FAMILY_SUBSCRIPTIONS?.endpoint;
 if(!endpoint){status.textContent='Email subscriptions are not available yet.';return}
 button.disabled=true;status.textContent='Requesting your confirmation email…';
 try{
  const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:fields.get('email'),topics,consent:fields.get('consent')==='on',website:fields.get('website')})});
  if(!response.ok)throw Error(response.status===429?'Please wait before requesting another confirmation.':'Your request could not be saved. Please try again.');
  status.textContent='Request received. Your confirmation email is queued for delivery within the next hour. Check your inbox and spam folder. Your subscription starts only after confirmation.';
 }catch(error){status.textContent=error.message==='Failed to fetch'?'We could not connect. Please try again shortly.':error.message}
 finally{button.disabled=false}
});
