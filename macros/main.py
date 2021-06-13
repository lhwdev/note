

def on_pre_page_macros(env):
	global env_meta
	env_meta = env.page.meta
	else: env_meta = ''


def define_env(env):
	
	@env.macro
	def head():
		return f'''
			<div style="color: --md-primary-fg-color--light; font-size: 13em;">
				{env_meta['date'] if 'date' in env else ''}
			</div>
		'''
