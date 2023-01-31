/* 
 *Lots of credit to this site, which forms the basis of the persistent features.
 * https://www.sitepoint.com/quick-tip-persist-checkbox-checked-state-after-page-reload/
 */

$(document).ready(function() {
    var persistentInputsValues = 
    	JSON.parse(localStorage.getItem("persistentInputsValues")) || {};
    var $persistentInputs = $(".promptKnob, #promptModelSelect");
    console.log($persistentInputs.length)
    
    $persistentInputs.on("change", function(){
      console.log("func called!");
      $persistentInputs.each(function(){
        persistentInputsValues[this.id] = this.value;
      });
      localStorage.setItem("persistentInputsValues", JSON.stringify(persistentInputsValues));
    });
    
    
    $.each(persistentInputsValues, function(key, value) {
      selection = $("#" + key);
      selection.prop('value', value);
      selection.each(function(){
        prevEl = this.previousElementSibling;
        if (prevEl !== null && (prevEl.className == "slider-out")){
          prevEl.value = this.value;
        }
      });
    });

});
