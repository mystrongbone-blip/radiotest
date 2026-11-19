var CACHE='shenqi-v2';
self.addEventListener('install',function(e){self.skipWaiting()});
self.addEventListener('activate',function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.map(function(k){if(k!==CACHE)return caches.delete(k)}));
  }).then(function(){return self.clients.claim()}));
});
self.addEventListener('fetch',function(e){
  var req=e.request;
  if(req.method!=='GET')return;
  var url=new URL(req.url);
  if(!/\.github\.io$/.test(url.hostname)&&url.origin!==location.origin)return;
  if(/script\.google|googleusercontent|googleapis/.test(url.hostname))return;
  if(req.headers.get('x-cy-preload')){e.respondWith(fetch(req));return}
  if(url.pathname.indexOf('version.txt')>-1){
    e.respondWith(fetch(req).then(function(r){
      var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)});return r;
    }).catch(function(){return caches.match(req)}));
    return;
  }
  if(/\/app\.html$/.test(url.pathname)){
    e.respondWith(caches.match(req).then(function(hit){
      return hit||fetch(req).then(function(r){
        if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
        return r;
      });
    }));
    return;
  }
  if(req.mode==='navigate'||/\.html?$/.test(url.pathname)){
    e.respondWith(fetch(req).then(function(r){
      if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
      return r;
    }).catch(function(){return caches.match(req)}));
    return;
  }
  e.respondWith(caches.match(req).then(function(hit){
    return hit||fetch(req).then(function(r){
      if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
      return r;
    });
  }));
});