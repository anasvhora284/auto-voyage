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
        // Set minimum date to today
        var today = new Date();
        var formattedDate =
            today.toISOString().split("T")[0] + "T" + today.toTimeString().split(" ")[0];
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
        var selectedDate = new Date(this.$("#scheduled_date").val());
        var now = new Date();

        // Remove any existing warnings
        this.$("#date-warning").remove();

        // Check if date is valid
        if (selectedDate < now) {
            this.$(
                '<div id="date-warning" class="alert alert-warning mt-2">Please select a future date and time.</div>'
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
