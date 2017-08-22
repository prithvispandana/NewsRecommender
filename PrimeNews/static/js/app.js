var app = angular.module('newsApp', ['ngRoute']); //angularjs in-built directive

app.config(function($routeProvider) { //router for single page application

	$routeProvider
	.when('/', { //default path
		templateUrl: "/home", //home.html is a view file to be display between header and footer of landing.html
	})

	// saved.html is the second view file to be display between header and footer of landing.html
	.when('/saved', {
		templateUrl: '/saved',
	})
	
	// searchpage.html is the third view file to be display between header and footer of landing.html

	.when('/searchpage', {
		templateUrl: '/searchpage',
	})
});

app.controller('mainCtrl', function($scope, $http, ajaxCall) { //main controller to control the flow of data in the application
	// mainCtrl takes care of all the data manipulation which includes like, dislike, saved, displaying more articles and so on.
	$scope.ArticlestoShow = []; //local storage scope variable
	$scope.saved = false;
	$scope.like = false;
	$scope.dislike = false;
	var savedArticle = [], alreadySaved = [], likedArticle=[], dislikedArticle = []; //variable to store the article ID when user click on bookmark, like and dislike icons 

//service method to get the recommended news 	
	ajaxCall.getMethod().then(function(respdata){ //ajax call for fetch the json file
		$scope.myNews= respdata; //myNews holds the whole json data
	});
	
	//search
	// Ajax call made to search the MongoDB database to find the Relative Articles for the Search keyword
	$scope.$watch('search',function () {
		 if ($scope.search!=null)
			 {
			 document.cookie=$scope.search
				  $http.post('/search', {search: $scope.search})// Takes the entered keyword and search in MongoDB database
				        .success(function (response) {
				            console.log('Happy searching!')
				            console.log(response)
				            $scope.Articlestosearch=response //assigns the list of search results to $scope variable for rendering them in the UI using angular JS
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
				            $scope.Articlestosearch=response//assigns the list of search results to $scope variable for rendering them in the UI using angular JS
					    document.getElementById('searchfield').value=document.cookie;
				        });	 
				}
			 
			 }

			
		})
	
	//function to be called to retrieve the article ID when user clicks bookmark icon
	$scope.isSaved = function(subset, event) { 
        console.log(subset._id.$oid)
        var target = angular.element(event.target);
        if (target.hasClass('saved') == false) {
            savedArticle.push(subset._id.$oid)
            console.log('userName', window.userName);
		
	    // saves the article ID into mongoDB along with keywords	
            $http.post('/usernews', {newsId: subset._id.$oid, userId: window.userName, keywords: subset.keywords})
                .success(function (response) {
                    console.log('saved')
                });
        }
    }

//If article is already saved, maintain the state
        $scope.alreadyMarked = function (subset) { //checks whether the article is already saved or not
            var breaks = false
            
            for (var i = 0; i < savedArticle.length; i++) {
                if (subset == savedArticle[i]) {
                    breaks = true;
                    break;
                }
            }
            if (breaks)
                return "saved"
        }

//all saved article of the user will be displayed using Ajax call	
        $scope.loadUserNews = function () {
            console.log('loading usernews ')
            var getresult = $http({
                method: 'GET',
                url: "/usernews/" + window.userName //Call made to get the stored user news for the particular user.
            }).then(function (response) {
                console.log(response.data)
                console.log("succ")
                $scope.ArticlestoShow = response.data
            }, function (response) {
                console.log("failure");
            });

        }


//function to be called to retrieve the article ID when user clicks the like icon and to save the liked article details into database
	$scope.liked = function(subset, $event){
		$($event.target).toggleClass('like');
		$($event.target).next().removeClass('dislike')
		console.log(subset._id.$oid)
		var target = angular.element(event.target);

		if(target.hasClass('like') ==true)
		{
			likedArticle.push(subset._id.$oid)
			console.log('userName', window.userName);
			$http.post('/likes', { newsId: subset._id.$oid, userId: window.userName, keywords: subset.keywords })
			.success(function () {
				console.log('saved')
			});
			
			// if a user dislikes an artilce, its ID is stored in dislikedArticle array. if the same user likes the same article later, its the article ID is removed from dislikedArticle array
			if(dislikedArticle.indexOf(subset._id.$oid) > -1){
				dislikedArticle.splice(dislikedArticle.indexOf(subset._id.$oid), 1 )

			}
		}
	}

//function to be called to retrieve the article ID when user clicks the dislike icon and to save the disliked article details into database
	$scope.disliked = function(subset, $event){
		$($event.target).toggleClass('dislike');
		$($event.target).prev().removeClass('like');
		var target = angular.element(event.target);
		if(target.hasClass('dislike') ==true){
			dislikedArticle.push(subset._id.$oid)
			console.log('userName', window.userName);
			$http.post('dislikes', { newsId: subset._id.$oid, userId: window.userName })// 
			.success(function(){
				console.log('saved')

			});
		}

		console.log(dislikedArticle)
	}



// function to fetch the similar article via ajax call when user hover over "more.."
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
				// calculating the position of the particular DOM, i.e., document object model to display the similar or embedded articles as a drop down list in the corresponding position
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


// factory has been defined for http request using $http directive 
app.factory('ajaxCall', function($http) { //ajax call to fetch /recom
	return {
		// getMethod returns data from the json file
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
