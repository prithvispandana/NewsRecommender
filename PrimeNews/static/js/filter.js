
// defining unique filter
app.filter('unique', function() {
  // return a function which will take in a collection and a keyname
   return k= function(collection, keyname) {
     // define output and keys array
      var output = [], 
          keys = [];

     // this takes in the original collection and an iterator function
      angular.forEach(collection, function(item) {
        // checks to see whether object exists irrespective of its letter case
          var key = item[keyname].trim().toLowerCase();
        // if it's not already part of our keys array
          if(keys.indexOf(key) === -1) {
            // add it to our keys array
              keys.push(key);
            // pushing the item to final array "output"
              output.push(item);
          }
      });
      k=output;
     // return the array "output" which should be free of any duplicates
      return output;
   };

});
