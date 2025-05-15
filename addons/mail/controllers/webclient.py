# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.addons.mail.controllers.thread import ThreadController
from odoo.addons.mail.tools.discuss import add_guest_to_context, Store


class WebclientController(http.Controller):
    """Routes for the web client."""

    @http.route("/mail/action", methods=["POST"], type="jsonrpc", auth="public")
    @add_guest_to_context
    def mail_action(self, fetch_params, context=None):
        """Execute actions and returns data depending on request parameters.
        This is similar to /mail/data except this method can have side effects.
        """
        return self._process_request(fetch_params, context=context)

    @http.route("/mail/data", methods=["POST"], type="jsonrpc", auth="public", readonly=True)
    @add_guest_to_context
    def mail_data(self, fetch_params, context=None):
        """Returns data depending on request parameters.
        This is similar to /mail/action except this method should be read-only.
        """
        return self._process_request(fetch_params, context=context)

    @classmethod
    def _process_request(self, fetch_params, context):
        store = Store()
        if context:
            request.update_context(**context)
        self._process_request_loop(store, fetch_params)
        return store.get_result()

    @classmethod
    def _process_request_loop(self, store: Store, fetch_params):
        for fetch_param in fetch_params:
            name, params, data_id = (
                (fetch_param, None, None)
                if isinstance(fetch_param, str)
                else (fetch_param + [None, None])[:3]
            )
            store.data_id = data_id
            self._process_request_for_all(store, name, params)
            if not request.env.user._is_public():
                self._process_request_for_logged_in_user(store, name, params)
            if request.env.user._is_internal():
                self._process_request_for_internal_user(store, name, params)
        store.data_id = None

    @classmethod
    def _process_request_for_all(self, store: Store, name, params):
        if name == "init_messaging":
            if not request.env.user._is_public():
                user = request.env.user.sudo(False)
                user._init_messaging(store)
        if name == "mail.thread":
            thread = ThreadController._get_thread_with_access(
                params["thread_model"],
                params["thread_id"],
                mode="read",
                **params.get("access_params", {}),
            )
            if not thread:
                store.add(
                    request.env[params["thread_model"]].browse(params["thread_id"]),
                    {"hasReadAccess": False, "hasWriteAccess": False},
                    as_thread=True,
                )
            else:
                store.add(thread, request_list=params["request_list"], as_thread=True)

    @classmethod
    def _process_request_for_logged_in_user(self, store: Store, name, params):
        if name == "failures":
            domain = [
                ("author_id", "=", request.env.user.partner_id.id),
                ("notification_status", "in", ("bounce", "exception")),
                ("mail_message_id.message_type", "!=", "user_notification"),
                ("mail_message_id.model", "!=", False),
                ("mail_message_id.res_id", "!=", 0),
            ]
            # sudo as to not check ACL, which is far too costly
            # sudo: mail.notification - return only failures of current user as author
            notifications = request.env["mail.notification"].sudo().search(domain, limit=100)
            notifications.mail_message_id._message_notifications_to_store(store)
        elif name == "load_messaging_menu_data":
            self._load_messaging_menu_data(store, params)

    @classmethod
    def _process_request_for_internal_user(self, store: Store, name, params):
        if name == "systray_get_activities":
            # sudo: bus.bus: reading non-sensitive last id
            bus_last_id = request.env["bus.bus"].sudo()._bus_last_id()
            groups = request.env["res.users"]._get_activity_groups()
            store.add_global_values(
                activityCounter=sum(group.get("total_count", 0) for group in groups),
                activity_counter_bus_id=bus_last_id,
                activityGroups=groups,
            )
        if name == "mail.canned.response":
            domain = [
                "|",
                ("create_uid", "=", request.env.user.id),
                ("group_ids", "in", request.env.user.all_group_ids.ids),
            ]
            store.add(request.env["mail.canned.response"].search(domain))

    @classmethod
    def _load_messaging_menu_data(self, store: Store, params: dict):
        """
        Load messaging menu data with advanced exclusion and filtering.

        :param store: Store object for caching
        :param params: Request parameters
        """
        tab = params.get("tab", "main")
        load_limit = int(params.get("limit", 20))
        previous_state = params.get("previous_state", {})
        exclusion_specs = {
            "message_thread_ids": params.get("exclude_message_thread_ids", []),
            "channel_thread_ids": params.get("exclude_channel_thread_ids", [])
        }
        tab_loaders = {
            "inbox": self._load_inbox_data,
            "channel": self._load_channel_data,
            "chat": self._load_chat_data,
            "main": self._load_main_data
        }
        loader = tab_loaders.get(tab)
        if loader:
            loader(store, load_limit, exclusion_specs, previous_state)

    @classmethod
    def _load_inbox_data(self, store: Store, limit: int, exclusions: dict, previous_state: dict):
        """
        Load data for the inbox tab.

        :param store: Store object
        :param limit: Maximum number of items to load
        :param exclusions: Dictionary of IDs to exclude
        :param previous_state: Previous loading state
        """
        inbox_domain = [
            ('needaction', '=', True),
            ('res_id', 'not in', exclusions.get('message_thread_ids', [])),
            ('model', '!=', 'discuss.channel')
        ]
        history_domain = [
            ('needaction', '=', False),
            ('res_id', 'not in', exclusions.get('message_thread_ids', [])),
            ('model', '!=', 'discuss.channel')
        ]
        inbox_result = request.env["mail.message"]._message_fetch(inbox_domain, limit=limit)
        inbox_msgs = inbox_result.get("messages", request.env["mail.message"])
        remaining_limit = limit - len(inbox_msgs)
        history_msgs = request.env["mail.message"]
        if remaining_limit > 0:
            history_result = request.env["mail.message"]._message_fetch(history_domain, limit=remaining_limit)
            history_msgs = history_result.get("messages", request.env["mail.message"])
        all_msgs = inbox_msgs + history_msgs
        store.add(all_msgs, for_current_user=True, add_followers=True)
        store.add_global_values(
            MessagingMenuRecordsLoadedState={
                **previous_state,
                "inbox": len(all_msgs) < limit
            }
        )

    @classmethod
    def _load_channel_data(self, store: Store, limit: int, exclusions: dict, previous_state: dict):
        """
        Load data for channels tab.

        :param store: Store object
        :param limit: Maximum number of items to load
        :param exclusions: Dictionary of IDs to exclude
        :param previous_state: Previous loading state
        """
        all_channels = request.env["discuss.channel"]._get_channels_as_member()
        all_channels = all_channels.filtered(lambda c: c.channel_type == "channel")
        excluded_ids = exclusions.get('channel_thread_ids', [])
        if excluded_ids:
            all_channels = all_channels.filtered(lambda c: c.id not in excluded_ids)
        all_channels._compute_message_needaction()
        needaction_channels = all_channels.filtered(lambda c: c.message_needaction)
        history_channels = all_channels.filtered(lambda c: not c.message_needaction)
        needaction_channels = needaction_channels.sorted(
            key=lambda c: c.last_interest_dt or datetime.min,
            reverse=True
        )
        history_channels = history_channels.sorted(
            key=lambda c: c.last_interest_dt or datetime.min,
            reverse=True
        )
        final_channels = (needaction_channels + history_channels)[:limit]
        request.update_context(
            channels=request.env.context["channels"] | final_channels, add_channels_last_message=True
        )
        store.add_global_values(
            MessagingMenuRecordsLoadedState={
                **previous_state,
                "channel": len(final_channels) < limit
            }
        )

    @classmethod
    def _load_chat_data(self, store: Store, limit: int, exclusions: dict, previous_state: dict):
        """
        Load data for chat tab.

        :param store: Store object
        :param limit: Maximum number of items to load
        :param exclusions: Dictionary of IDs to exclude
        :param previous_state: Previous loading state
        """
        all_channels = request.env["discuss.channel"]._get_channels_as_member()
        all_channels = all_channels.filtered(lambda c: c.channel_type in ["chat", "group"])
        excluded_ids = exclusions.get('channel_thread_ids', [])
        if excluded_ids:
            all_channels = all_channels.filtered(lambda c: c.id not in excluded_ids)
        needaction_channels = all_channels.filtered(lambda c: c.message_needaction)
        history_channels = all_channels.filtered(lambda c: not c.message_needaction)
        needaction_channels = needaction_channels.sorted(
            key=lambda c: c.last_interest_dt or datetime.min,
            reverse=True
        )
        history_channels = history_channels.sorted(
            key=lambda c: c.last_interest_dt or datetime.min,
            reverse=True
        )
        final_channels = (needaction_channels + history_channels)[:limit]
        request.update_context(
            channels=request.env.context["channels"] | final_channels, add_channels_last_message=True
        )
        store.add_global_values(
            MessagingMenuRecordsLoadedState={
                **previous_state,
                "chat": len(final_channels) < limit
            }
        )

    @classmethod
    def _load_main_data(self, store: Store, limit: int, exclusions: dict, previous_state: dict):
        """
        Load data for main tab with comprehensive thread and message fetching.

        :param store: Store object
        :param limit: Maximum number of items to load
        :param exclusions: Dictionary of IDs to exclude
        :param previous_state: Previous loading state
        """
        unread_message_domain = [
            ('needaction', '=', True),
            ('res_id', 'not in', exclusions.get('message_thread_ids', [])),
            ('model', '!=', 'discuss.channel')
        ]
        unread_message_result = request.env["mail.message"]._message_fetch(unread_message_domain)
        unread_messages = unread_message_result.get("messages", request.env["mail.message"])
        all_channels = request.env["discuss.channel"]._get_channels_as_member()
        all_channels = all_channels.filtered(lambda c: c.channel_type in ['chat', 'group', 'channel'])
        excluded_ids = exclusions.get('channel_thread_ids', [])
        if excluded_ids:
            all_channels = all_channels.filtered(lambda c: c.id not in excluded_ids)
        needaction_channels = all_channels.filtered(lambda c: c.message_needaction)
        not_needaction_channels = all_channels.filtered(lambda c: not c.message_needaction)

        def get_sort_key(record):
            date_val = None
            if record._name == 'discuss.channel':
                date_val = record.last_interest_dt
            elif record._name == 'mail.message':
                date_val = record.write_date
            return date_val or datetime.datetime.min
        combined_all_unread = []
        combined_all_unread.extend(unread_messages)
        combined_all_unread.extend(needaction_channels)
        sorted_all_unread = sorted(
            combined_all_unread,
            key=get_sort_key,
            reverse=True
        )
        sorted_all_read = sorted(
            not_needaction_channels,
            key=get_sort_key,
            reverse=True
        )
        sorted_all_threads_list = []
        sorted_all_threads_list.extend(sorted_all_unread)
        sorted_all_threads_list.extend(sorted_all_read)
        limited_threads_list = sorted_all_threads_list[:limit]
        final_messages = request.env["mail.message"]
        final_channels = request.env["discuss.channel"]
        for record in limited_threads_list:
            if record._name == 'mail.message':
                final_messages |= record
            elif record._name == 'discuss.channel':
                final_channels |= record
        if final_messages:
            store.add(final_messages, for_current_user=True, add_followers=True)
        if final_channels:
            request.update_context(
                channels=request.env.context["channels"] | final_channels, add_channels_last_message=True
            )
        total_added_count = len(limited_threads_list)
        all_loaded_for_this_call = total_added_count < limit
        state_update = {
            **previous_state,
            "main": all_loaded_for_this_call,
            'channel': all_loaded_for_this_call,
            'chat': all_loaded_for_this_call
        }
        store.add_global_values(MessagingMenuRecordsLoadedState=state_update)
