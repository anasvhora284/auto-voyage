import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

const AutoVoyageBooking = publicWidget.Widget.extend({
  selector: ".o_auto_voyage_booking_form",
  events: {
    "change #service_id": "_onServiceChange",
    "change #vehicle_id": "_onVehicleChange",
    "change #scheduled_date": "_validateDate",
  },

  /**
   * @override
   */
  start: function () {
    var self = this;
    return this._super.apply(this, arguments).then(function () {
      self._initializeForm();
    });
  },

  /**
   * Initialize the booking form with default values and setup
   * @private
   */
  _initializeForm: function () {
    // Set minimum date to today (format YYYY-MM-DDThh:mm)
    var today = new Date();

    // Round minutes to the nearest 5 minutes to avoid odd time values
    var minutes = Math.ceil(today.getMinutes() / 5) * 5;
    today.setMinutes(minutes);
    today.setSeconds(0);
    today.setMilliseconds(0);

    var formattedDate = today.toISOString().slice(0, 16);
    this.$("#scheduled_date").attr("min", formattedDate);

    // Initialize service details section if a service is already selected
    if (this.$("#service_id").val()) {
      this._onServiceChange();
    }
  },

  /**
   * Handle service selection change
   * @private
   */
  _onServiceChange: function () {
    var selectedOption = this.$("#service_id option:selected");
    var price = selectedOption.data("price");
    var duration = selectedOption.data("duration");

    if (price) {
      this.$("#service-price").text(price.toFixed(2));
      this.$("#service-duration").text(duration);
      this.$("#service-details").removeClass("d-none");
    } else {
      this.$("#service-details").addClass("d-none");
    }
  },

  /**
   * Handle vehicle selection change
   * @private
   */
  _onVehicleChange: function () {
    var vehicleId = this.$("#vehicle_id").val();
    if (!vehicleId) {
      // Show warning if no vehicle selected
      if (!this.$("#vehicle-warning").length) {
        this.$(
          '<div id="vehicle-warning" class="alert alert-warning mt-2">Please select a vehicle to continue.</div>'
        ).insertAfter("#vehicle_id");
      }
    } else {
      // Remove warning if vehicle is selected
      this.$("#vehicle-warning").remove();
    }
  },

  /**
   * Validate the selected date
   * @private
   */
  _validateDate: function () {
    // Get the selected date and current date
    var selectedDateStr = this.$("#scheduled_date").val();

    // If no date is selected, don't validate
    if (!selectedDateStr) {
      return true;
    }

    var selectedDate = new Date(selectedDateStr);
    var now = new Date();

    // Remove any existing warnings
    this.$("#date-warning").remove();

    // Set seconds and milliseconds to 0 for both dates to avoid comparison issues
    selectedDate.setSeconds(0);
    selectedDate.setMilliseconds(0);

    now.setSeconds(0);
    now.setMilliseconds(0);

    // Add 5 minutes to current time for buffer
    var bufferTime = new Date(now.getTime() + 5 * 60000);

    if (selectedDate < bufferTime) {
      this.$(
        '<div id="date-warning" class="alert alert-warning mt-2">Please select a future date and time (at least 5 minutes from now).</div>'
      ).insertAfter("#scheduled_date");
      return false;
    }

    // Check if the date is on a Sunday (when the shop might be closed)
    if (selectedDate.getDay() === 0) {
      this.$(
        '<div id="date-warning" class="alert alert-warning mt-2">Note: We are closed on Sundays. Please select another day or contact us for special arrangements.</div>'
      ).insertAfter("#scheduled_date");
    }

    return true;
  },
});

publicWidget.registry.AutoVoyageBooking = AutoVoyageBooking;

export default AutoVoyageBooking;
3;
