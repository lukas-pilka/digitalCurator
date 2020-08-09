

// artwork focused

(function(){
	function hasClass(el, cls) {
		if (el.className.match('(?:^|\\s)'+cls+'(?!\\S)')) { return true; }
		}
	function addClass(el, cls) {
		if (!el.className.match('(?:^|\\s)'+cls+'(?!\\S)')) { el.className += ' '+cls; }
		}
	function delClass(el, cls) {
		el.className = el.className.replace(new RegExp('(?:^|\\s)'+cls+'(?!\\S)'),'');
		}

	function elementFromLeft(elem, classToAdd, distanceFromLeft, unit) {
		var winX = window.innerWidth || document.documentElement.clientWidth,
		elemLength = elem.length, distLeft, distPercent, distPixels, distUnit, i;
		for (i = 0; i < elemLength; ++i) {
			distLeft = elem[i].getBoundingClientRect().left;
			distPercent = Math.round((distLeft / winX) * 100);
			distPixels = Math.round(distLeft);
			distUnit = unit == 'percent' ? distPercent : distPixels;
			if (distUnit <= distanceFromLeft) {
				if (!hasClass(elem[i], classToAdd)) { addClass(elem[i], classToAdd); }
				} else {
				delClass(elem[i], classToAdd);
				}
			}
		}
	// params: element, classes to add, distance from top, unit ('percent' or 'pixels')

	window.addEventListener('scroll', function() {
		elementFromLeft(document.querySelectorAll('.artwork'),       'focuseIn',       30, 'percent'); // as left of element hits left of viewport
		elementFromLeft(document.querySelectorAll('.artwork'),       'focuseOut',       10, 'percent'); // as left of element hits left of viewport
		}, false);

	window.addEventListener('resize', function() {
		elementFromLeft(document.querySelectorAll('.artwork'),       'focuseIn',       30, 'percent'); // as left of element hits left of viewport
		elementFromLeft(document.querySelectorAll('.artwork'),       'focuseOut',       10, 'percent'); // as left of element hits left of viewport
		}, false);
})();