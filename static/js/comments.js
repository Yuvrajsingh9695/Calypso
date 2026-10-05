document.addEventListener("DOMContentLoaded", function () {

    /*
     * ============================================================
     * AJAX COMMENT SYSTEM
     * ============================================================
     *
     * Handles:
     *
     * - Post comment
     * - Like comment
     * - Unlike comment
     * - Reply
     * - Like reply
     * - Unlike reply
     * - Delete comment
     * - Delete reply
     *
     * Only the comments component is replaced.
     * The movie/TV page itself is NOT refreshed.
     */


    /*
     * ============================================================
     * CSRF TOKEN
     * ============================================================
     */

    function getCSRFToken(form) {

        const csrfInput = form.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        if (csrfInput) {
            return csrfInput.value;
        }

        return "";
    }


    /*
     * ============================================================
     * SHOW LOADING STATE
     * ============================================================
     */

    function setLoading(form, loading) {

        const button = form.querySelector(
            'button[type="submit"]'
        );

        if (!button) {
            return;
        }

        if (loading) {

            if (!button.dataset.originalText) {
                button.dataset.originalText = button.innerHTML;
            }

            button.disabled = true;

            button.innerHTML = `
                <span
                    class="spinner-border spinner-border-sm me-1"
                    role="status"
                    aria-hidden="true"
                ></span>
                Processing...
            `;

        } else {

            button.disabled = false;

            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            }

        }
    }


    /*
     * ============================================================
     * REPLACE COMMENT COMPONENT
     * ============================================================
     */

    function replaceComments(html) {

        const currentComponent = document.querySelector(
            "#comments-component"
        );

        if (!currentComponent) {
            return;
        }

        /*
         * Convert returned HTML into a real DOM element.
         */

        const wrapper = document.createElement("div");

        wrapper.innerHTML = html.trim();

        const newComponent = wrapper.querySelector(
            "#comments-component"
        );

        if (!newComponent) {
            console.error(
                "Could not find #comments-component in AJAX response."
            );

            return;
        }

        /*
         * Replace only the comments component.
         */

        currentComponent.replaceWith(
            newComponent
        );
    }


    /*
     * ============================================================
     * AJAX FORM SUBMISSION
     * ============================================================
     */

    async function submitCommentForm(form) {

        const url = form.action;

        const formData = new FormData(form);

        setLoading(
            form,
            true
        );

        try {

            const response = await fetch(
                url,
                {
                    method: "POST",

                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json",
                    },

                    body: formData,

                    credentials: "same-origin",
                }
            );


            /*
             * If Django returned an error status,
             * don't silently pretend everything worked.
             */

            if (!response.ok) {

                throw new Error(
                    `Server returned ${response.status}`
                );
            }


            const data = await response.json();


            if (!data.success) {

                throw new Error(
                    "The server reported that the operation failed."
                );
            }


            /*
             * Replace only the comments component.
             */

            replaceComments(
                data.html
            );


            /*
             * Scroll gently back toward the comments section.
             */

            const commentsComponent = document.querySelector(
                "#comments-component"
            );

            if (commentsComponent) {

                commentsComponent.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });

            }


        } catch (error) {

            console.error(
                "AJAX comment error:",
                error
            );


            /*
             * If something goes wrong, fall back to
             * the normal form submission.
             *
             * This keeps the feature usable even if
             * JavaScript or the AJAX response has an issue.
             */

            form.submit();

        } finally {

            /*
             * The form may have been replaced already.
             * setLoading is safe because it only works
             * with the original form reference.
             */

            setLoading(
                form,
                false
            );

        }

    }


    /*
     * ============================================================
     * EVENT DELEGATION
     * ============================================================
     *
     * The comments component gets replaced after every AJAX
     * operation. Therefore we must NOT attach event listeners
     * directly to individual forms.
     *
     * Instead, listen on the document.
     */

    document.addEventListener(
        "submit",
        function (event) {

            const form = event.target.closest(
                ".ajax-comment-form"
            );

            if (!form) {
                return;
            }

            /*
             * Stop the browser's normal form submission.
             */

            event.preventDefault();


            /*
             * Send using fetch().
             */

            submitCommentForm(
                form
            );

        }
    );

});
