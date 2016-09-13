// first approach, get the latest id and add new one increment of prev one
// second approach, get all item and then loop through all of them

// adding new form dynamically
// get last .transaction-item
var lastItem = $('.transaction-item:last');

// clone into new one and put it after the last item
lastItem.clone(true).insertAfter(lastItem);

// get last index of item (even though it should be 0 every time it loads)
var lastItemId = /\d+/.exec(lastItem.attr('id'));

// and change all its value depending on the loop index
// change the form value all into next number
var indexedElements = lastItem.find('[id^=transaction_items-],[for^=transaction_items-]');

// change every attribute number
// for id, name, for
function changeItemAttr() {
  var idAttr = $(this).attr('id');
  var nameAttr = $(this).attr('name');
  var forAttr = $(this).attr('for');

  if (typeof idAttr != 'undefined') {
    $(this).attr('id', idAttr.replace(/\d+/, lastItemId));
  }

  if (typeof nameAttr != 'undefined') {
    $(this).attr('name', nameAttr.replace(/\d+/, lastItemId));
  }

  if (typeof forAttr != 'undefined') {
    $(this).attr('for', forAttr.replace(/\d+/, lastItemId));
  }

}

indexedElements.each(changeItemAttr);

$('[id^=transaction_items-]').each(function() {
  $(this).attr('id', $(this).attr('id').replace(/\d+/, lastItemId));
  $(this).attr('name', $(this).attr('name').replace(/\d+/, lastItemId));
});

$('[for^=transaction_items-]').each(function() {
  $(this).attr('for', $(this).attr('for').replace(/\d+/, lastItemId));
})
