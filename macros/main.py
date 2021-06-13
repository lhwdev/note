

def on_pre_page_macros(env):
	global env_meta
	env_meta = env.page.meta


def define_env(env):
	
	@env.macro
	def head():
		return f'''<div style="color: var(--md-primary-fg-color--light); font-size: small;">{env_meta.get('date', '')}</div>'''
