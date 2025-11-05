// FizzBuzz implementation in legacy JavaScript style
// Using var declarations, function declarations, and older ES5 patterns

function fizzbuzz() {
  var i;
  var output = "";

  // Classic for loop with var declaration
  for (i = 1; i <= 100; i++) {
    var result = "";

    // Check divisibility using modulo operator
    if (i % 3 === 0) {
      result += "Fizz";
    }
    if (i % 5 === 0) {
      result += "Buzz";
    }

    // If no Fizz or Buzz, use the number
    if (result == "") {
      result = i.toString();
    }

    // Legacy string concatenation instead of template literals
    output += result + "\n";

    // Also log to console for immediate feedback
    console.log(result);
  }

  return output;
}

// Legacy function call pattern
var result = fizzbuzz();

// Legacy comment style explaining the algorithm
/*
 * FizzBuzz Rules:
 * - Print numbers 1 to 100
 * - For multiples of 3, print "Fizz"
 * - For multiples of 5, print "Buzz"
 * - For multiples of both 3 and 5, print "FizzBuzz"
 * - Otherwise print the number itself
 */

// Alternative legacy implementation using switch statement
function fizzbuzzAlternative(max) {
  var counter = 1;

  while (counter <= max) {
    var output = "";

    // Legacy approach using multiple conditions
    if (counter % 15 == 0) {
      output = "FizzBuzz";
    } else if (counter % 3 == 0) {
      output = "Fizz";
    } else if (counter % 5 == 0) {
      output = "Buzz";
    } else {
      output = counter;
    }

    console.log(output);
    counter = counter + 1; // Legacy increment style
  }
}

// Uncomment to run alternative version
// fizzbuzzAlternative(100);
