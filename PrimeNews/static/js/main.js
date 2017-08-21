$(document).ready(function(){
	alert("body")
setTimeout(function(){
$('.bxslider').bxSlider({
  minSlides: 3,
  maxSlides: 3,
  slideWidth: 360,
  slideMargin: 1,
  moveSlides: 2,
  pager: false
});
},1000);

$('.slide-title').css('width',$('.display-img').width())

	});
