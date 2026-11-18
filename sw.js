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
  if(/script\.google|googleusercontent|googleapis/.test(url.hostname))return;   /* 金鑰驗證直連 */

  /* 外殼的預載請求:放行,由外殼自己存快取 */
  if(req.headers.get('x-cy-preload')){e.respondWith(fetch(req));return}

  /* 版本檔:一律走網路,失敗才用快取 */
  if(url.pathname.indexOf('version.txt')>-1){
    e.respondWith(fetch(req).then(function(r){
      var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)});return r;
    }).catch(function(){return caches.match(req)}));
    return;
  }
  /* 神器本體:快取優先(由外殼維護),沒有才上網 */
  if(/\/app\.html$/.test(url.pathname)||req.mode==='navigate'&&/\/app\.html/.test(url.href)){
    e.respondWith(caches.match(req).then(function(hit){
      return hit||fetch(req).then(function(r){
        if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
        return r;
      });
    }));
    return;
  }
  /* 外殼自己:網路優先(保持外殼最新),離線退快取 */
  if(req.mode==='navigate'||/\.html?$/.test(url.pathname)){
    e.respondWith(fetch(req).then(function(r){
      if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
      return r;
    }).catch(function(){return caches.match(req)}));
    return;
  }
  /* 其他靜態檔(圖示、sim 圖庫):快取優先,自動補 */
  e.respondWith(caches.match(req).then(function(hit){
    return hit||fetch(req).then(function(r){
      if(r.ok){var cp=r.clone();caches.open(CACHE).then(function(c){c.put(req,cp)})}
      return r;
    });
  }));
});