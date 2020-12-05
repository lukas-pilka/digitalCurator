// popup window

function openMenu() {
  let element = document.getElementById("menuSecondLevel");
  element.classList.toggle("opened");
  let element2 = document.getElementById("wrapper");
  element2.classList.toggle("behindFog");
  let element3 = document.getElementById("jsMenuIcon");
  element3.classList.toggle("opened");
  let element4 = document.getElementById("jsSearchWindow");
  element4.classList.remove("opened");
  let element5 = document.getElementById("jsAboutWindow");
  element5.classList.remove("opened");
}
function openSearch() {
  let element = document.getElementById("jsSearchWindow");
  element.classList.toggle("opened");
  let element2 = document.getElementById("jsMenuWindow");
  element2.classList.toggle("opened");
}
function openAbout() {
  let element = document.getElementById("jsAboutWindow");
  element.classList.toggle("opened");
  let element2 = document.getElementById("jsMenuWindow");
  element2.classList.toggle("opened");
}

// Open popup window with search forms if contains error messages

function checkErrors() {
	let isError = document.getElementsByClassName('errorMessage');
	if (isError.length > 0) {
		openMenu()
		openSearch()
	}
}

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

	function elementFromTop(elem, classToAdd, distanceFromTop, unit) {
		var winY = window.innerHeight || document.documentElement.clientHeight,
		elemLength = elem.length, distTop, distPercent, distPixels, distUnit, i;
		for (i = 0; i < elemLength; ++i) {
			distTop = elem[i].getBoundingClientRect().top;
			distPercent = Math.round((distTop / winY) * 100);
			distPixels = Math.round(distTop);
			distUnit = unit == 'percent' ? distPercent : distPixels;
			if (distUnit <= distanceFromTop) {
				if (!hasClass(elem[i], classToAdd)) { addClass(elem[i], classToAdd); }
				} else {
				delClass(elem[i], classToAdd);
				}
			}
		}
	// params: element, classes to add, distance from top, unit ('percent' or 'pixels')

	if(window.innerWidth <= 960) {
		window.addEventListener('scroll', function () {
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as top of element hits top of viewport
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent'); // as top of element hits top of viewport
		}, false);
		window.addEventListener('resize', function () {
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as top of element hits top of viewport
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent'); // as top of element hits top of viewport
		}, false);
	}else{
		window.addEventListener('scroll', function () {
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as left of element hits left of viewport
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent'); // as left of element hits left of viewport
		}, false);
		window.addEventListener('resize', function () {
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as left of element hits left of viewport
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent'); // as left of element hits left of viewport
		}, false);
	}

})();