"use strict";

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

class ServiceBookingForm extends publicWidget.Widget {
    selector = ".service-booking-form";
    events = {
        'change select[name="service_id"]': "_onServiceChange",
        'change select[name="vehicle_id"]': "_onVehicleChange",
        'change input[name="scheduled_date"]': "_onDateChange",
        "click .btn-book": "_onBookClick",
    };

    async start() {
        await super.start();
        this._initializeForm();
    }

    _initializeForm() {
        this._updateServiceDetails();
        this._updateAvailableSlots();
    }

    _onServiceChange(ev) {
        this._updateServiceDetails();
    }

    _onVehicleChange(ev) {
        this._updateAvailableSlots();
    }

    _onDateChange(ev) {
        this._updateAvailableSlots();
    }

    async _updateServiceDetails() {
        const serviceId = this.$('select[name="service_id"]').val();
        if (!serviceId) return;

        const result = await this._rpc({
            route: "/service/details",
            params: {
                service_id: serviceId,
            },
        });

        if (result) {
            this.$(".service-price").text(result.price);
            this.$(".service-duration").text(result.duration);
            this.$(".service-description").text(result.description);
        }
    }

    async _updateAvailableSlots() {
        const serviceId = this.$('select[name="service_id"]').val();
        const vehicleId = this.$('select[name="vehicle_id"]').val();
        const date = this.$('input[name="scheduled_date"]').val();

        if (!serviceId || !vehicleId || !date) return;

        const result = await this._rpc({
            route: "/service/available-slots",
            params: {
                service_id: serviceId,
                vehicle_id: vehicleId,
                date: date,
            },
        });

        if (result) {
            const $slots = this.$('select[name="scheduled_time"]');
            $slots.empty();

            result.slots.forEach((slot) => {
                $slots.append(
                    $("<option>", {
                        value: slot.value,
                        text: slot.label,
                    })
                );
            });
        }
    }

    _onBookClick(ev) {
        ev.preventDefault();

        if (!this._validateForm()) {
            return;
        }

        this._rpc({
            route: "/service/book",
            params: this._getFormData(),
        }).then((result) => {
            if (result.success) {
                window.location.href = result.redirect_url;
            } else {
                this._showError(result.message);
            }
        });
    }

    _validateForm() {
        let isValid = true;
        const $form = this.$("form");

        $form.find("select[required], input[required]").each(function () {
            if (!$(this).val()) {
                isValid = false;
                $(this).addClass("is-invalid");
            } else {
                $(this).removeClass("is-invalid");
            }
        });

        if (!isValid) {
            this._showError(_t("Please fill in all required fields."));
        }

        return isValid;
    }

    _getFormData() {
        const data = {};
        this.$("form")
            .serializeArray()
            .forEach((item) => {
                data[item.name] = item.value;
            });
        return data;
    }

    _showError(message) {
        const $alert = $("<div>", {
            class: "alert alert-danger alert-dismissible fade show",
            role: "alert",
            html:
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>',
        });

        this.$(".form-errors").html($alert);
        setTimeout(() => {
            $alert.alert("close");
        }, 5000);
    }
}

// Service Provider Search
class ProviderSearch extends publicWidget.Widget {
    selector = ".provider-search";
    events = {
        'input input[name="search"]': "_onSearchInput",
        'change select[name="expertise"]': "_onExpertiseChange",
        'change select[name="rating"]': "_onRatingChange",
    };

    async start() {
        await super.start();
        this._initializeSearch();
    }

    _initializeSearch() {
        this._debouncedSearch = _.debounce(this._performSearch.bind(this), 500);
    }

    _onSearchInput(ev) {
        this._debouncedSearch();
    }

    _onExpertiseChange(ev) {
        this._performSearch();
    }

    _onRatingChange(ev) {
        this._performSearch();
    }

    async _performSearch() {
        const searchData = {
            query: this.$('input[name="search"]').val(),
            expertise: this.$('select[name="expertise"]').val(),
            rating: this.$('select[name="rating"]').val(),
        };

        const result = await this._rpc({
            route: "/providers/search",
            params: searchData,
        });

        if (result) {
            this._updateResults(result);
        }
    }

    _updateResults(providers) {
        const $container = this.$(".provider-results");
        $container.empty();

        providers.forEach((provider) => {
            const $card = $(qweb.render("ProviderCard", { provider }));
            $container.append($card);
        });
    }
}

// Contact Form
class ContactForm extends publicWidget.Widget {
    selector = ".contact-form";
    events = {
        submit: "_onSubmit",
    };

    async start() {
        await super.start();
        this._initializeForm();
    }

    _initializeForm() {
        this.$("form").on("submit", this._onSubmit.bind(this));
    }

    _onSubmit(ev) {
        ev.preventDefault();

        if (!this._validateForm()) {
            return;
        }

        this._rpc({
            route: "/contact/submit",
            params: this._getFormData(),
        }).then((result) => {
            if (result.success) {
                this._showSuccess(result.message);
                this.$("form")[0].reset();
            } else {
                this._showError(result.message);
            }
        });
    }

    _validateForm() {
        let isValid = true;
        const $form = this.$("form");

        $form.find("input[required], textarea[required]").each(function () {
            if (!$(this).val()) {
                isValid = false;
                $(this).addClass("is-invalid");
            } else {
                $(this).removeClass("is-invalid");
            }
        });

        if (!isValid) {
            this._showError(_t("Please fill in all required fields."));
        }

        return isValid;
    }

    _getFormData() {
        const data = {};
        this.$("form")
            .serializeArray()
            .forEach((item) => {
                data[item.name] = item.value;
            });
        return data;
    }

    _showSuccess(message) {
        const $alert = $("<div>", {
            class: "alert alert-success alert-dismissible fade show",
            role: "alert",
            html:
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>',
        });

        this.$(".form-messages").html($alert);
        setTimeout(() => {
            $alert.alert("close");
        }, 5000);
    }

    _showError(message) {
        const $alert = $("<div>", {
            class: "alert alert-danger alert-dismissible fade show",
            role: "alert",
            html:
                message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>',
        });

        this.$(".form-messages").html($alert);
        setTimeout(() => {
            $alert.alert("close");
        }, 5000);
    }
}

// Initialize all widgets
publicWidget.registry.ServiceBookingForm = ServiceBookingForm;
publicWidget.registry.ProviderSearch = ProviderSearch;
publicWidget.registry.ContactForm = ContactForm;
