import os
import ipywidgets as widgets
from IPython.display import display, clear_output
from newspaper import Article
from llm_models_api.chat_gpt.chatgpt_api import get_response_from_chatgpt
from llm_models_api.deepseek.deepseek_api import get_response_from_deepseek

# podcast에 적합한 버전
def llm_system_role_podcast():
    return "Your task is to analyze raw crolling content from web news articles, " + \
           "remove any irrelevant noise, and extract the following: \n" + \
           "1. The NEW TITLE of the article for a podcast, \n" + \
           "2. The 'detailed organized in a way that is suitable for a podcast' contents of the article 'excepting noise like e-mail address or copyright or figure description...', and \n" + \
           "3. A list of the most important keywords of the article. \n" + \
           "OUTPUT ELEMENT FORMAT shoud be 3 as 'TITLE:' 'CONTENTS:' 'KEYWORDS:'\n" + \
           "Focus on 'accuracy', 'removing noise'."+ \
           "without comment please"


def llm_system_role_summary():
    return "Your task is to analyze raw crawling content from web news articles, " + \
           "remove any irrelevant noise, and extract the following in a structured format: \n" + \
           "1. **TITLE:** A concise and descriptive title summarizing the main topic of the article. \n" + \
           "2. **CONTENTS:** A well-structured summary that captures key details, background information, and broader implications. " + \
           "Use bullet points if necessary to enhance clarity, and remove any noise such as e-mail addresses, copyright notices, or figure descriptions. \n" + \
           "3. **KEYWORDS:** A list of the most relevant keywords, separated by commas, that summarize the core topics of the article. \n" + \
           "Ensure 'accuracy' and 'noise removal'. \n" +\
           "without comment please"


def make_croll_result(article):
    return f'''title: {article.title}
result: {article.text}
'''


def user_prompt(contents):
    return f'''
raw web ARTICLE is here: 

{contents}
'''


def translate_prompt(lang):
    return f'''
TRANSLATE into {lang}
'''


def make_article(url, lang):
    article = Article(url, language=lang)
    article.download()
    article.parse()
    return article


def write_result(output_dir, filename, result_list):
    os.makedirs(output_dir, exist_ok=True)
    cur_output_file_path = f"{output_dir}/{filename}.txt"
    with open(cur_output_file_path, "w") as file:
        file.writelines(result_list)
    print(f"SUCCESS to write at {cur_output_file_path}")


def run(filename, urls, input_lang, ouput_lang, llm_model, croll_ouput_dir,
        llm_podcast_output_dir, llm_summary_output_dir, output_widget):
    with output_widget:
        clear_output()
        url_list = urls.split(',')
        valid_url_list = []
        for url in url_list:
            try:
                cur_article = make_article(url, input_lang)
                len_cur_article = len(cur_article.text)
                if len_cur_article < 300:
                    print(f"{url} crolling contents is too small: {len_cur_article}, skip this news")
                    continue
                valid_url_list.append(url)
            except Exception as e:
                print(f"{url} crolling failed, skip this news", e)

        print("")
        print("input url count: ", len(url_list))
        print("valid url count for crolling: ", len(valid_url_list))
        print("")

        llm_podcast_role = llm_system_role_podcast()
        llm_summary_role = llm_system_role_summary()

        _save_podcast_result = llm_podcast_output_dir != ''
        _save_summary_result = llm_summary_output_dir != ''

        print("start to clean and extract (news title, news contents, news main keywords)...", llm_model)
        print("")

        if _save_podcast_result:
            print("LLM PODCAST ROLE SETTING:")
            print(llm_podcast_role)
            print("")

        if _save_summary_result:
            print("LLM SUMMARY ROLE SETTING:")
            print(llm_summary_role)
            print("")

        croll_result_list = []
        llm_podcast_result_list = []
        llm_summary_result_list = []
        success_count = 0
        _need_translate = False
        if input_lang == 'ko':
            if ouput_lang != 'KOREAN':
                _need_translate = True
        elif input_lang == 'en':
            if ouput_lang != 'ENGLISH':
                _need_translate = True
        else:
            raise ValueError(f"not supported input lang: {input_lang}")

        for idx, url in enumerate(valid_url_list):
            cur_article = make_article(url, input_lang)

            croll_result = make_croll_result(cur_article)
            croll_result_list.append(croll_result)
            if idx != len(valid_url_list) - 1:
                croll_result_list.append("\n\n" + "-" * 3 + "\n\n")

            cur_prompt_list = [user_prompt(croll_result)]
            if _need_translate:
                cur_prompt_list.append(translate_prompt(ouput_lang))
            try:
                if llm_model.startswith("gpt"):
                    if _save_podcast_result:
                        llm_podcast_result_list.append(
                            get_response_from_chatgpt(llm_podcast_role, cur_prompt_list, model=llm_model))
                    if _save_summary_result:
                        llm_summary_result_list.append(
                            get_response_from_chatgpt(llm_summary_role, cur_prompt_list, model=llm_model))
                elif llm_model.startswith("deepseek"):
                    if _save_podcast_result:
                        llm_podcast_result_list.append(
                            get_response_from_deepseek(llm_podcast_role, cur_prompt_list, model=llm_model))
                    if _save_summary_result:
                        llm_summary_result_list.append(
                            get_response_from_deepseek(llm_summary_role, cur_prompt_list, model=llm_model))
                else:
                    raise ValueError(f"not supported llm model: {llm_model}")
            except Exception as e:
                print(f"failed to extract (news title, news contents, news main keywords) {url}", e)
                continue
            success_count += 1
            if idx != len(valid_url_list) - 1:
                if _save_podcast_result:
                    llm_podcast_result_list.append("\n\n" + "-" * 3 + "\n\n")
                if _save_summary_result:
                    llm_summary_result_list.append("\n\n" + "-" * 3 + "\n\n")

        print("SUCCESS to extract (news title, news contents, news main keywords)e from LLM!: ", success_count)

        if croll_ouput_dir != '' and len(croll_result_list) != 0:
            write_result(croll_ouput_dir, f"{filename}_croll", croll_result_list)

        if _save_podcast_result and len(llm_podcast_result_list) != 0:
            write_result(llm_podcast_output_dir, f"{filename}_podcast", llm_podcast_result_list)

        if _save_summary_result and len(llm_summary_result_list) != 0:
            write_result(llm_summary_output_dir, f"{filename}_summary", llm_summary_result_list)

# --- Build the GUI using ipywidgets ---

# Define the widgets for the parameters
file_name_widget = widgets.Text(
    value='output',
    description='File Name:',
    placeholder='Enter file name'
)

urls_widget = widgets.Textarea(
    value='https://example.com/news1, https://example.com/news2',
    description='URLs:',
    placeholder='Enter one or more URLs, separated by commas',
    layout=widgets.Layout(width='100%', height='80px')
)

input_lang_widget = widgets.Dropdown(
    options=[('Korean', 'ko'), ('English', 'en')],
    value='ko',
    description='Input Lang:'
)

output_lang_widget = widgets.Dropdown(
    options=[('Korean', 'KOREAN'), ('English', 'ENGLISH')],
    value='ENGLISH',
    description='Output Lang:'
)

llm_model_widget = widgets.Dropdown(
    options=['gpt-4o-mini', 'gpt-4o', 'deepseek-chat', 'deepseek-reasoner'],
    value='gpt-4o-mini',
    description='LLM Model:'
)

croll_output_dir_widget = widgets.Text(
    value='crawl_results',
    description='Crawl Dir:',
    placeholder='Directory for crawl output'
)

llm_podcast_output_dir_widget = widgets.Text(
    value='llm_podcast_results',
    description='Podcast Dir:',
    placeholder='Directory for podcast output'
)

llm_summary_output_dir_widget = widgets.Text(
    value='llm_summary_results',
    description='Summary Dir:',
    placeholder='Directory for summary output'
)

run_button = widgets.Button(
    description='Run Process',
    button_style='success'
)

output_area = widgets.Output()

# Define the button click callback
def on_run_button_clicked(b):
    run(
        filename=file_name_widget.value,
        urls=urls_widget.value,
        input_lang=input_lang_widget.value,
        ouput_lang=output_lang_widget.value,
        llm_model=llm_model_widget.value,
        croll_ouput_dir=croll_output_dir_widget.value,
        llm_podcast_output_dir=llm_podcast_output_dir_widget.value,
        llm_summary_output_dir=llm_summary_output_dir_widget.value,
        output_widget=output_area
    )

run_button.on_click(on_run_button_clicked)

# Display the GUI
display(
    file_name_widget,
    urls_widget,
    input_lang_widget,
    output_lang_widget,
    llm_model_widget,
    croll_output_dir_widget,
    llm_podcast_output_dir_widget,
    llm_summary_output_dir_widget,
    run_button,
    output_area
)
