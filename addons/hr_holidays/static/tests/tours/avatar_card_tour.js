import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("avatar_card_tour", {
    url: "/odoo/discuss",
    steps: () => [
        {
            content: "Open the chat",
            trigger: ".o-mail-DiscussSidebar-item:contains(Test User)",
            run: "click",
        },
        {
            content: "Open the avatar card popover",
            trigger: ".o-mail-Message-avatar",
            run: "click",
        },
        {
            content: "Check that the employee's work email is displayed",
            trigger:
                ".o_avatar_card:contains(test_employee@test.com):contains(Back on):contains(987654321):contains(Test Department):contains(Test Job Title)",
        },
    ],
});
