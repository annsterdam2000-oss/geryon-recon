# agent/modules/__init__.py
from .email import module_email
from .email_reg import module_email_reg
from .domain import module_domain
from .http_check import module_http_check
from .ip import module_ip
from .phone import module_phone
from .person import module_person

MODULE_FUNCS = {
    "email": module_email,
    "email_reg": module_email_reg,
    "domain": module_domain,
    "http_check": module_http_check,
    "ip": module_ip,
    "phone": module_phone,
    "person": module_person,
}