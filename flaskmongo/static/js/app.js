var app = angular.module('newsApp', ['ngRoute']);

app.config(function($routeProvider) {

    $routeProvider
        .when('/', {
            templateUrl: "/home"
        })

        // saved
        .when('/saved', {
            templateUrl: '/saved.html',
            controller: 'mainCtrl'
        })

});

app.controller('mainCtrl', function($scope, $http, ajaxCall) {
	setTimeout(function() {
        $('.bxslider').bxSlider({
            minSlides: 3,
            maxSlides: 3,
            slideWidth: 360,
            slideMargin: 1,
            moveSlides: 2 
        });
    }, 6000);
    $scope.ArticlestoShow = [];
    $scope.saved = false;
    $scope.like = false;
    $scope.dislike = false;
    var savedArticle = [];
    ajaxCall.getMethod().then(function(respdata) {
        $scope.myNews = respdata;
    });


    $scope.isSaved = function(s, event) {
        console.log(s._id.$oid)
        var target = angular.element(event.target);
        if (target.hasClass('saved') == false) {
            savedArticle.push(s._id.ObjectId)
        } else {
            if ((savedArticle.indexOf(s._id.$oid)) > -1) {
                savedArticle.splice(savedArticle.indexOf(s._id.$oid), 1)
            }
        }
        $scope.ArticlestoShow = savedArticle;
        console.log($scope.ArticlestoShow)
    }



});

app.factory('ajaxCall', function($http) {
    return {
    	
        getMethod: function() {
            var getresult = $http({
                method: 'GET',
                url: "/recom"
            }).then(function(response) {
                console.log("success")
                return response.data;
            }, function(response) {
                console.log("failure");
            });
            return getresult;
        }
    };
});