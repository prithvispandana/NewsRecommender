//var fileInterval = setInterval(function(){
//    if (functionInFile){
//			alert("hello")
//        // do something
//        clearInterval(fileInterval); // clear interval
//    }
//},3000);
setInterval(function(){
	$('.bxslider').bxSlider({
        minSlides: 3,
        maxSlides: 3,
        slideWidth: 360,
        slideMargin: 1,
        moveSlides: 2 
    });
},100);