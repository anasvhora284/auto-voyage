"use strict";

import publicWidget from "@web/legacy/js/public/public_widget";

class RatingStars extends publicWidget.Widget {
  selector = ".rating-stars-container";
  events = {
    "click .rating-stars label": "_onStarClick",
  };

  /**
   * @override
   */
  async start() {
    await super.start();
    this._updateStars();
    return this;
  }

  /**
   * Updates the stars display based on the currently selected rating
   * @private
   */
  _updateStars() {
    // First, reset all stars to default color
    const allStars = this.el.querySelectorAll(".rating-stars i");
    allStars.forEach((star) => {
      star.style.color = "#ccc";
    });

    // Then highlight the selected stars
    const checkedInputs = this.el.querySelectorAll(
      ".rating-stars input:checked"
    );

    checkedInputs.forEach((input) => {
      // Since we're using flex-direction: row-reverse, we need to highlight
      // the selected star and all stars AFTER it in the DOM
      const label = input.nextElementSibling;
      const star = label.querySelector("i");

      if (star) {
        star.style.color = "#FFD700";
      }

      // In the reversed layout, we need to color all labels AFTER this one
      let nextLabel = label;
      while ((nextLabel = nextLabel.nextElementSibling)) {
        if (nextLabel.tagName === "LABEL") {
          const nextStar = nextLabel.querySelector("i");
          if (nextStar) {
            nextStar.style.color = "#FFD700";
          }
        }
      }
    });
  }

  /**
   * Handles star click events
   * @private
   * @param {Event} ev
   */
  _onStarClick(ev) {
    const label = ev.currentTarget;
    const input = label.previousElementSibling;
    const value = input.value;
    const ratingText = this.el.querySelector("#quality-rating-text");

    if (ratingText) {
      ratingText.textContent = value;
    }

    // With flex-direction: row-reverse, we need to update our coloring logic
    // Let the CSS handle the coloring through the :checked selector
    // Just make sure the input is checked
    input.checked = true;

    // Trigger an input event to notify any listeners
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }
}

publicWidget.registry.RatingStars = RatingStars;

export default RatingStars;
