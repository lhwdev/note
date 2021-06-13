

def on_pre_page_macros(env):
	global env_meta
	env_meta = env.page.meta


def define_env(env):
	
	@env.macro
	def head():
		return f'''<div style="color: var(--md-default-fg-color--light); font-size: small; padding: -4px 0 12px 0;">{env_meta.get('date', '')}</div>'''
