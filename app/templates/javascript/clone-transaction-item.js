var itemId = 0;

  $(function () {
    // store the initial item id depending on how many in the page
    itemId = $('.transaction-item').length
    modifyRemoveBtnStatus();

    // save the raw clone
    // benefit: so cloned one can be .chosen()
    // also the new one will have empty data instead of filled one
    var rawClone = $('.transaction-item:first').clone().trigger("reset");
    rawClone.find('[id^=transaction_items-]').each(function() {
      $(this).attr('value', '');
    });

    // add event to add-item button
    $('#add-item').click(function () {
      // var newItem = $('.transaction-item:last').clone().insertAfter($('.transaction-item:last'));
      var newItem = $(rawClone).clone().insertAfter($('.transaction-item:last'));

      // change value of new item
      itemId++;

      newItem.find('[id^=transaction_items-]').each(function () {
        replaceAttr($(this), 'id', /\d+/, itemId);
        replaceAttr($(this), 'name', /\d+/, itemId);
      });

      newItem.find('[for^=transaction_items-]').each(function () {
        replaceAttr($(this), 'for', /\d+/, itemId);
      });

      newItem.find('[id$=_item_type_chosen]').each(function() {
        replaceAttr($(this), 'id', /\d+/, itemId);
      })

      $('select').chosen();
      modifyRemoveBtnStatus();
    });

    // add event to remove-item button
    $('#remove-item').click(function () {
      $('.transaction-item:last').remove();
      itemId--;

      modifyRemoveBtnStatus();
    });

    // chosen is: https://github.com/harvesthq/chosen add chosen in to select field set chosen settings
    $('select').chosen({no_results_text: "Ooops!! Nothing found"});

  });

  function replaceAttr(obj, attrName, toBeReplaced, replacement) {
    obj.attr(attrName, obj.attr(attrName).replace(toBeReplaced, replacement));
  }

  // this one will enable and disable remove button
  function modifyRemoveBtnStatus() {
    var removeBtn = $('#remove-item');
    if (itemId > 1) { // more than 1 item listed in html

      // remove disabled in removeBtn if exists
      if (removeBtn.hasClass('disabled')) {
        removeBtn.removeClass('disabled');
      }

    } else { // only 1 item listed in html

      // add disabled in remove Btn class
      if (!removeBtn.hasClass('disabled')) {
        removeBtn.addClass('disabled');
      }

    }
  }