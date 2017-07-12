
//filter
app.filter('unique', function() {
  
   return k= function(collection, keyname) {
      var output = [], 
          keys = [];

      angular.forEach(collection, function(item) {
          var key = item[keyname].trim().toLowerCase();
          if(keys.indexOf(key) === -1) {
              keys.push(key);
              output.push(item);
          }
      });
      k=output;
      return output;
   };

});