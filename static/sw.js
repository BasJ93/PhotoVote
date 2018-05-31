var CACHE_NAME = 'PhotoVote-cache-v1';
	var urlsToCache = [
		'/',
		'/index.css',
		'/jquery.star-rating-svg.js',
		'/star-rating-svg.css',
		'/login',
		'/sorry.html'
		];

self.addEventListener('install', function(event) {
	event.waitUntil(
		caches.open(CACHE_NAME)
			.then(function(cache)
			{
				console.log('Opened cache');
				return cache.addAll(urlsToCache)
					.catch(function(error)
					{
						console.log(error);
					});
			}
		)
	);
});

self.addEventListener('fetch', function(event) {
	event.respondWith(
		caches.match(event.request)
			.then(function(response) {
				if (response) {
					return response;
				}
				return fetch(event.request)
					.catch(function(error)
						{
							return caches.match('/sorry.html');
						});
			}
		)
	);
});
