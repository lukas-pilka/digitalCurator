// global variables

let splash = document.getElementById("sharingPopup"); // Get a reference to the sharing window
let container = document.getElementById("container");
let mainMenu = document.getElementById("mainMenu");

// horizontal scrolling with wheel

container.addEventListener('wheel', (ev) => {
	ev.preventDefault();  // stop scrolling in another direction
	// console.log(ev.deltaY);
	container.scrollLeft += (ev.deltaY + ev.deltaX);
	// console.log('Wheel Move: '+ container.scrollLeft);
});

// horizontal scrolling with arrow keys

document.addEventListener('keydown', function(event) {
	if (event.code == 'ArrowRight') {
		container.style.scrollBehavior = 'smooth';
		container.scrollLeft += 500;
		container.style.scrollBehavior = null;
  	}
  	if (event.code == 'ArrowLeft') {
  		container.style.scrollBehavior = 'smooth';
    	container.scrollLeft -= 500;
    	container.style.scrollBehavior = null;
  	}
});

// scroll progress

container.addEventListener('scroll', handleScroll);

function handleScroll() {
    let winScroll = container.scrollLeft || container.documentElement.scrollLeft;
    let width = container.scrollWidth - container.clientWidth;
    let scrolled = (winScroll / width) * 100;

    document.getElementById("progressBar").style.width = scrolled + "%";
}

// sharing window

function closeWindow() {
	let element = document.getElementById("sharingPopup");
	element.classList.toggle("closed"); // add class closed
	let d = new Date();
	let xDays = 1 // * Duration in days
	d.setTime(d.getTime() + (xDays * 24 * 60 * 60 * 1000));
	let expires = "expires=" + d.toGMTString();
	document.cookie = "visited=true;" + expires; // Creating cookie when closing window
	container.classList.toggle("blurred");
	mainMenu.classList.toggle("blurred");
}
window.addEventListener("load", function () {
	if (document.cookie.indexOf("visited=true") === -1) { // Check to see if the cookie indicates a first-time visit
		setTimeout(function () { // Reveal the window after delay
			splash.classList.remove("closed");
			container.classList.toggle("blurred");
			mainMenu.classList.toggle("blurred");
		}, 20000); // set delay in ms
	}
});

// get urls for sharing

window.onload = function() {
	let fbLink = document.getElementsByClassName("jsFbShare");
	let fb;
	for (fb = 0; fb < fbLink.length; fb++) {
	  fbLink[fb].href ='http://www.facebook.com/share.php?u=' + encodeURIComponent(location.href);
	}
	let twLink = document.getElementsByClassName("jsTwShare");
	let tw;
	for (tw = 0; tw < twLink.length; tw++) {
	  twLink[tw].href ='https://twitter.com/share?url=' + encodeURIComponent(location.href);
	}
}

// menu & search window

function openBackgroundCover() {
	let element1 = document.getElementById("menuCover");
	element1.classList.add("opened");
	let element2 = document.getElementById("container");
	if(element2 !== null) {
		element2.classList.add("blurred");
	}
}
function closeBackgroundCover() {
	let element1 = document.getElementById("menuCover");
	element1.classList.remove("opened");
	let element2 = document.getElementById("container");
	if(element2 !== null) {
		element2.classList.remove("blurred");
	}
}
function closeMenu() {
	closeBackgroundCover()
	let element5 = document.getElementById("menuSecondLevel");
	element5.classList.remove("opened");
	let element2 = document.getElementById("jsCloseMenu");
	element2.classList.remove("visible");
	let element3 = document.getElementById("jsOpenMenu");
	element3.classList.add("visible");
}
function closeSearch() {
	closeBackgroundCover()
	let element1 = document.getElementById("jsSearchWindow");
	element1.classList.remove("opened");
	let element2 = document.getElementById("jsCloseSearch");
	element2.classList.remove("visible");
	let element3 = document.getElementById("jsOpenSearch");
	element3.classList.add("visible");
}
function openSearch() {
	closeMenu();
	openBackgroundCover()
	let element1 = document.getElementById("jsSearchWindow");
	element1.classList.add("opened");
	let element2 = document.getElementById("jsCloseSearch");
	element2.classList.add("visible");
	let element3 = document.getElementById("jsOpenSearch");
	element3.classList.remove("visible");
}
function openMenu() {
	closeSearch();
	openBackgroundCover()
	let element1 = document.getElementById("menuSecondLevel");
	element1.classList.toggle("opened");
	let element2 = document.getElementById("jsCloseMenu");
	element2.classList.add("visible");
	let element3 = document.getElementById("jsOpenMenu");
	element3.classList.remove("visible");
}

// Open popup window with search forms if contains error messages

function checkErrors() {
	let isError = document.getElementsByClassName('errorMessage');
	if (isError.length > 0) {
		openMenu()
		openSearch()
	}
}
checkErrors()

// Copy url

function copyUrl() {
	if (!window.getSelection) {
		alert('Please copy the URL from the location bar.');
		return;
	}
	const dummy = document.createElement('p');
	dummy.textContent = window.location.href;
	document.body.appendChild(dummy);

	const range = document.createRange();
	range.setStartBefore(dummy);
	range.setEndAfter(dummy);

	const selection = window.getSelection();
	// First clear, in case the user already selected some other text
	selection.removeAllRanges();
	selection.addRange(range);

	document.execCommand('copy');
	document.body.removeChild(dummy);

	let htmlElement = document.getElementsByClassName("jsCopyLink");
	let i;
	for (i = 0; i < htmlElement.length; i++) {
	  htmlElement[i].classList.add("done");
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
		let container = document.getElementById("container");
		let winX = container.innerWidth || document.documentElement.clientWidth,
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
		let container = document.getElementById("container");
		let winY = container.innerHeight || document.documentElement.clientHeight,
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

	if(container.offsetWidth <= 960) {
		container.addEventListener('scroll', function () {
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as top of element hits top of viewport
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent');
		}, false);
		container.addEventListener('resize', function () {
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as top of element hits top of viewport
			elementFromTop(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent');
		}, false);
	}
	else{
		container.addEventListener('scroll', function () {
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as left of element hits left of viewport
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent');
			elementFromLeft(document.querySelectorAll('.visionFrame'), 'focuseIn', 45, 'percent');
			elementFromLeft(document.querySelectorAll('.galleryRecognition'), 'focuseIn', 60, 'percent');
			elementFromLeft(document.querySelectorAll('.galleryRecognition'), 'focuseOut', -60, 'percent');
		}, false);
		container.addEventListener('resize', function () {
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseIn', 50, 'percent'); // as left of element hits left of viewport
			elementFromLeft(document.querySelectorAll('.artwork'), 'focuseOut', 30, 'percent');
			elementFromLeft(document.querySelectorAll('.visionFrame'), 'focuseIn', 45, 'percent');
			elementFromLeft(document.querySelectorAll('.galleryRecognition'), 'focuseIn', 60, 'percent');
			elementFromLeft(document.querySelectorAll('.galleryRecognition'), 'focuseOut', -60, 'percent');
		}, false);
	}
})();

// parallax

function parallax(elementId, shift, speed) {
  if(document.body.clientWidth >= 960) {
    let canvas = document.getElementById(elementId);
    let XPos = shift - container.scrollLeft * speed;
    canvas.style.left = 0 + XPos + "%";
  }
}
container.addEventListener("scroll", function () {
	parallax('introGallery',0, 0.015);
	parallax('introMap',30,0.015);
	parallax('upperLine',150,0.05);
});

// title screen animation

const target = document.querySelector('.titlePart h1');
	target.innerHTML = target.textContent
		.replace(/\w+,|\w+|-|'|\./g, '<span data-glitch="$&">$&</span>');

const target2 = document.querySelector('.titlePart .subtitle');
target2.innerHTML = target2.textContent
	.replace(/\w+,|\w+|-|&|'|\./g, '<span data-glitch="$&">$&</span>');






