import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

console.log("AutoVoyagePortal widget loaded", publicWidget);
/**
 * AutoVoyagePortal Widget
 */
const AutoVoyagePortal = publicWidget.Widget.extend({
    selector: ".o_auto_voyage_portal",

    /**
     * @override
     */
    start: function () {
        console.log("AutoVoyagePortal widget start method called");
        return this._super.apply(this, arguments).then(() => {
            this._initializeRatingStars();
        });
    },

    /**
     * Initialize the rating stars
     * @private
     */
    _initializeRatingStars: function () {
        this.$(".rating-stars input").on("change", (event) => {
            const value = $(event.currentTarget).val();
            const stars = $(event.currentTarget).closest(".rating-stars").find("i");

            stars.each(function (index) {
                if (index < value) {
                    $(this).removeClass("fa-star-o").addClass("fa-star");
                } else {
                    $(this).removeClass("fa-star").addClass("fa-star-o");
                }
            });
        });
    },
});

publicWidget.registry.AutoVoyagePortal = AutoVoyagePortal;

export default AutoVoyagePortal;
