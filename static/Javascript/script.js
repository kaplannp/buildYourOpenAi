/* 
 *Lots of credit to this site, which forms the basis of the persistent features.
 * https://www.sitepoint.com/quick-tip-persist-checkbox-checked-state-after-page-reload/
 */

$(document).ready(function() {
    console.log("running!");
    
    var promptKnobValues = 
    	JSON.parse(localStorage.getItem("promptKnobValues")) || {};
    var $promptKnobs = $(".promptKnob");
    
    $promptKnobs.on("change", function(){
      console.log("func called!");
      $promptKnobs.each(function(){
        promptKnobValues[this.id] = this.value;
      });
      localStorage.setItem("promptKnobValues", JSON.stringify(promptKnobValues));
    });
    
    
    $.each(promptKnobValues, function(key, value) {
      selection = $("#" + key);
      selection.prop('value', value);
      selection.each(function(){
	this.previousElementSibling.value = this.value
      });
    });
    
    console.log(JSON.parse(localStorage.getItem("promptKnobValues")));
    
});
