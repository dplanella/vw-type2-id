var csrftoken = Cookies.get('csrftoken');

function submitForm(event) {

  // Prevent execution of the form's
  // default submit action
  event.preventDefault();

  var form = $(this);
  var url = form.attr('action');

  function apply_form_field_error(form_id, fieldname, error) {

    var input_selector = "#" + form_id + " #id_" + fieldname;
    var input = $(input_selector);

    // Mark the input as invalid (red frame)
    input.addClass("is-invalid");

    // Display the error message
    $("<p/>", {
      id: "error_1_id_" + fieldname,
      "class": "invalid-feedback",
      text: error
    }).html('<strong>' + error + '</strong>').insertAfter(input);

  }

  function clear_form_field_errors(form) {
    $(".invalid-feedback", $(form)).remove();
    $(".is-invalid", $(form)).removeClass("is-invalid");
  }

  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  $.ajax({
    type: "POST",
    url: url,
    data: form.serialize(),
    dataType: 'json',
    context: this,
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
      clear_form_field_errors(form);
    },
    success: function(data) {
      window.location.href = "/mplate/" + data.chassis_number_short;
    },
    error: function(response) {
      // TODO: check status code (response.status), apply error classes on 400 only
      var form_errors = response.responseJSON;

      for (field in form_errors) {
        error = form_errors[field][0].message;
        apply_form_field_error(this.id, field, error);
      }
    }
  });
};

$("#mplate_form_6869").submit(submitForm);
$("#mplate_form_7079").submit(submitForm);
