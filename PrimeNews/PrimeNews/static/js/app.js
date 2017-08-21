var app = angular.module('newsApp', ['ngRoute']); //angularjs in-built directive

app.config(function($routeProvider) { //router for single page application

	$routeProvider
	.when('/', { //default path
		templateUrl: "/home", //home.html is a view file
	})

	// saved
	.when('/saved', {
		templateUrl: '/saved',
	})

	.when('/searchpage', {
		templateUrl: '/searchpage',
	})
});

app.controller('mainCtrl', function($scope, $http, ajaxCall) { //main controller
	$scope.ArticlestoShow = []; //local storage scope variable
	$scope.saved = false;
	$scope.like = false;
	$scope.dislike = false;
	var savedArticle = [], alreadySaved = [], likedArticle=[], dislikedArticle = []; //variable to store the saved article and already saved article

//service method to get the recommended news 	
	ajaxCall.getMethod().then(function(respdata){ //ajax call for fetch the date from sample.json
		$scope.myNews= respdata; //myNews holds the whole json data
	});
	
	//search
	
	$scope.$watch('search',function () {
		 if ($scope.search!=null)
			 {
			 document.cookie=$scope.search
				  $http.post('/search', {search: $scope.search})
				        .success(function (response) {
				            console.log('Happy searching!')
				            console.log(response)
				            $scope.Articlestosearch=response
				            window.location = "/#/searchpage/"
				        });	 
			 }
		 else
			 {
			 if(document.cookie!=null)
				{
				  $http.post('/search', {search: document.cookie})
				        .success(function (response) {
				            console.log('Happy searching!')
				            console.log(response)
				            $scope.Articlestosearch=response
							document.getElementById('searchfield').value=document.cookie;
				        });	 
				}
			 
			 }

			
		})
	
//This method saved the all bookmarked article into database	
	$scope.isSaved = function(subset, event) { //function to fetch the saved article from localstorage and will be used in saved.html page
        console.log(subset._id.$oid)
        var target = angular.element(event.target);
        if (target.hasClass('saved') == false) {
            savedArticle.push(subset._id.$oid)
            console.log('userName', window.userName);

            $http.post('/usernews', {newsId: subset._id.$oid, userId: window.userName, keywords: subset.keywords})
                .success(function (response) {
                    console.log('saved')
                });
        }
    }

//If article is already saved maintatin the state
        $scope.alreadyMarked = function (subset) { //to check whether the article is already saved or not
            var breaks = false
            //var subset = subsets._id.$oid
            for (var i = 0; i < savedArticle.length; i++) {
                if (subset == savedArticle[i]) {
                    breaks = true;
                    break;
                }
            }
            if (breaks)
                return "saved"
        }

//all saved article of the user will be displayed	
        $scope.loadUserNews = function () {
            console.log('loading usernews ')
            var getresult = $http({
                method: 'GET',
                url: "/usernews/" + window.userName
            }).then(function (response) {
                console.log(response.data)
                console.log("succ")
                $scope.ArticlestoShow = response.data
            }, function (response) {
                console.log("failure");
            });

        }


//To save the liked article into database
	$scope.liked = function(subset, $event){
		$($event.target).toggleClass('like');
		$($event.target).next().removeClass('dislike')
		console.log(subset._id.$oid)
		var target = angular.element(event.target);

		if(target.hasClass('like') ==true)
		{
			likedArticle.push(subset._id.$oid)
			// savedArticle.push(subset._id.$oid)
			console.log('userName', window.userName);
			$http.post('/likes', { newsId: subset._id.$oid, userId: window.userName, keywords: subset.keywords })
			.success(function () {
				console.log('saved')
			});

			if(dislikedArticle.indexOf(subset._id.$oid) > -1){
				dislikedArticle.splice(dislikedArticle.indexOf(subset._id.$oid), 1 )

			}
		}
	}

//to save the disliked article into database
	$scope.disliked = function(subset, $event){
		$($event.target).toggleClass('dislike');
		$($event.target).prev().removeClass('like');
		var target = angular.element(event.target);
		if(target.hasClass('dislike') ==true){
			dislikedArticle.push(subset._id.$oid)
			console.log('userName', window.userName);
			$http.post('dislikes', { newsId: subset._id.$oid, userId: window.userName })
			.success(function(){
				console.log('saved')

			});
		}

		console.log(dislikedArticle)
	}



//Method to fetch the similar article and create the popup
	$scope.othersDisplay =function(subset, $event){
		console.log("others")
		$http.post('/simNews',subset)
		.then(function(response){
			$scope.othersdetails=response.data
			console.log("others");
			console.log(response.data);

			if($scope.othersdetails.length>0){
				dummyvar = true;
				$('.display-popup').removeClass('hide');
				//calcuating the position
				$('.display-popup').css({'top':($($event.target).offset().top + $($event.target).height()) + 10,
					'left':  ($($event.target).offset().left - $('.display-popup').width()/2)});
				$('.display-popup').mouseleave(function() {
					$('.display-popup').addClass('hide');
				});
				
				 //hides the popup when user hover the slider
				  $('.bx-controls-direction a').mouseover(function(){
				    $('.display-popup').addClass('hide');
				  });	

			}
			$scope.currentPage = 0;
			$scope.pageSize = 3;
			//calculating no. of pages
			$scope.numberOfPages=function(){
				return Math.ceil($scope.othersdetails.length/$scope.pageSize);                
			}

		}) 
	}

});


//This call is made to fetch recommended article
app.factory('ajaxCall', function($http) { //ajax call to fetch /recom
	return {
		getMethod: function() {
			var getresult = $http({
				method: 'GET',
				url: "/recom"
			}).then(function(response) {
				console.log("success")
				console.log(response.data)
				return response.data;
			}, function(response) {
				console.log("failure");
			});
			return getresult;
		}
	};
});

//pagination
app.filter('firstPage', function() {
	return function(input, start) {
		start = +start;
		return input &&input.slice(start);
	}
});
