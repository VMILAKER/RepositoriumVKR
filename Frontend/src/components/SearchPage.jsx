import { useEffect, useLayoutEffect, useState, useRef } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom';
import { Button, Form, Input, Select, Space,List, Card, Spin, Collapse,Modal, InputNumber, Popover, notification } from 'antd';
import {InfoCircleOutlined} from '@ant-design/icons'
import * as util from './Utilities.jsx';
import FingerprintJS from '@fingerprintjs/fingerprintjs';


function App_main() {
  const { Option } = Select;
  const refContainer= useRef(null);
  const [dataGQW, setGQW] = useState(util.initialFormState);
  const [gqwForm, setGqwData] = useState([]);
  const [filter, setFilter] = useState(0);
  const [isLoading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [api, contextHolder_notification] = notification.useNotification();
  const [getThemes, setThemes] = useState([]);
  const [getSupervisors, setSupervisors] = useState([]);
  const [getTags, setTags] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [getVisitorUpload, uploadVisitor] = useState(util.uploadKey);
  const [visitor, setVisitor] = useState(util.checkKey);
  const [passkey, setPasskey] = useState([]);
  const [modal, contextHolder_modal] = Modal.useModal();
  const [widthB, setWidth] = useState(0);

  const modalConfig = (item, theme) => {
    visitor['vkr_id'] = item
    getVisitorUpload['vkr_id'] = item
    
    modal.confirm({
      title: 'Получить полную версию ВКР',
      closable: {'aria-label': 'Custom Close Button' },
      width: 450,
      state: {blur: false},
      okText: 'Проверить ключ',
      onOk() {getVkrByPasskey(backend_url, visitor, headers)},
      cancelText: "Отмена",
      onCancel() {handleCancel},
      content: (
        <div>
          <Input ref={refContainer} className='my-2' name="passkey" placeholder='Введите ключ доступа' onChange={inputPasskey} allowClear/>  
          <Button style={{width: 370}} color="primary" variant='solid' onClick={() => uploadPasskey(backend_url, getVisitorUpload, theme, headers)}>Получить ключ доступа к полному тексту ВКР</Button>
        </div>
        )
      
    })
  }
  const backend_url = import.meta.env.VITE_BACKEND_URL;
  const pdf_external_url = import.meta.env.VITE_FRONTEND_EXTERNAL_URL;
  const api_key = import.meta.env.VITE_API_KEY;
  const compressed_path = import.meta.env.VITE_COMPRESSED_PATH;
  const abstract_path = import.meta.env.VITE_ABSTRACT_PATH;
 
  const headers = {'API_Key': api_key}


  const openNotificationWithIcon = (type, param) => {
    api[type]({
      description:
        param,
    });
  };
  
  const get_visitor_id = async() => {
    // const FingerprintJS = await import('https://openfpcdn.io/fingerprintjs/v5');
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    
    if (result && result.visitorId) {
      const id = result.visitorId.toString();
      setVisitor({...visitor, visitor_id: id})
      uploadVisitor({...getVisitorUpload, visitor_id: id})
    }
  };
  

  const fetchPrior = async(url_) => {
    try {
      let getOptions = [];
      await axios.get(`${url_}/get_preloaded_data`, {headers}).then(r => {
        getOptions = r.data
        if (getOptions.length > 0) {
          setThemes(getOptions[0])
          setSupervisors(getOptions[3])
          setTags(getOptions[5])
        }
      })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };
 
  useEffect(() => {
    fetchPrior(backend_url)
    get_visitor_id()
  }, [backend_url]);
  
  useLayoutEffect(() => {
    if (refContainer.current) {
      setWidth(refContainer.current.offsetWidth)
    }
  }, []);

  const fetchData = async(dataGQW, url_) => {   
    setLoading(true) 
    const params = {}

    for (let i in dataGQW) {
      if (dataGQW[i]) {
        params[i] = dataGQW[i]
      }
    }

    try {
      await axios.get(`${url_}/get_vkr`, {params:params, headers:headers} ).then(r => {
        let response = r.data
        if ((response.length >= 2) && (!(response == 'No data')) && (!(response == "No findings by tag's query"))) {
          response.sort(function (a,b) {
          if (a?.theme < b?.theme) {
            return -1;
          }
          if (a?.theme > b?.theme) {
            return 1;
          }
          return 0;
          })
        }
        setGqwData(response)
        setLoading(false)
      })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };
  
  const uploadPasskey = async(url_, param, theme_name, headers) => { 
    try {
      await axios.post(`${url_}/add_passkey`, param, {headers:headers}).then(r => {
        let response_from_add_passkey = r.data
        openNotificationWithIcon('info', `Ваш пароль для '${theme_name}': ${response_from_add_passkey}`)
        getPasskeyInitial(url_, param, headers)
        paramsShow(gqwForm, gqwForm.length, passkey)
      })
      setIsModalOpen(false);
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const getPasskeyInitial = async(url_, param, headers) => {
    try {
       await axios.get(`${url_}/get_initial_passkeys`, {params:param, headers:{...headers}} ).then(r => {
        let resp = r.data
        if (!(resp == 'No data'))
          setPasskey(resp)
       })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const getVkrByPasskey = async(url_, param, headers) => {
    try {
      let resp =''
      await axios.get(`${url_}/get_vkr_by_passkey`, {params:param, headers:headers}).then(r => {
        resp = r.data})
      if (!(resp == 'No data') && !(resp == 'Unvalid key')) {
        await axios.post(`${url_}/add_passkey`, param, {headers:headers}).then(r=> {
          getPasskeyInitial(url_, param, headers)
          openNotificationWithIcon('success', 'Успешно добавлена полная версия')
          paramsShow(gqwForm, gqwForm.length, passkey)
        })
        setIsModalOpen(false);   
        visitor['password'] = ''     
      }
      else {
        openNotificationWithIcon('error', 'Неправильный ключ')
        setIsModalOpen(false); 
      }
    }
    
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const handleCancel = (target) => {
    visitor['password'] = ''
    target.value = ''
    
    setIsModalOpen(false);
  };

  const handleSubmit = async event => {
    event.preventDefault()
  };

  const handleChange = (event) => {
    setGQW({...dataGQW, [event.target.name]: event.target.value})
  };

  const SelectChange_theme = (event) => {
    let theme_list = []
    theme_list.push(event)
    setGQW({...dataGQW, theme: theme_list.join(',')})
  };

  const SelectChange_qualification = (event) => {
    setGQW({...dataGQW, qualification: event})
  };

  const SelectChange_supervisor = (event) => {
    let superv_list = []
    superv_list.push(event)
    setGQW({...dataGQW, supervisor: superv_list.join(',')})
  };


  const SelectChange_tags = (event) => {
    let tag_list = []
    tag_list.push(event)
    setGQW({...dataGQW, tags:tag_list.join(',')})
  };

  const handleChangeFilter_top = (event) => {
    setFilter(event*1)
  };

  const inputPasskey = (event) => {
    visitor['password'] = event.target.value
  };

  const onReset = () => {
    form.resetFields();
    setGQW(util.initialFormState)
    setFilter(0)
  };
  
  const saveLink = (filename, bucket_type) => {
    localStorage.setItem("filename", filename)
    localStorage.setItem("bucket_type", bucket_type)
  };
  
  const check_key_card = (key_list, param, reference) => { 
      
      if (Array.from(key_list).find((o) => o?.id == param)) {
        return (
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: </span><a className='text-justify' href={`${pdf_external_url}/pdf_viewer`} onClick={() => saveLink(reference, compressed_path)} target="_blank" >Полный текст</a>/ <a className='text-justify' href={`${pdf_external_url}/pdf_viewer`} onClick={() => saveLink(reference, abstract_path)} target="_blank" >Аннотация</a></p>
        )}
      else {
        return (
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: <a className='text-justify' href={`${pdf_external_url}/pdf_viewer`} onClick={() => saveLink(reference, abstract_path)} target="_blank" >Аннотация</a></span></p>
          )
        }
    };

  function CardVKR(item, key_list) {
    const tag_array = (param) => {
      return param.join(', ')
    };

    return( 
      <>
        <Card component='span' styles={{'title':{'textWrap': "wrap"}}} title={item?.theme}>
          <div className='flex items-center'><span className='font-bold mr-2'>Руководитель: </span><Collapse className='w-130' size='small' items={[{label:item?.supervisor, children: <ul><li>Место работы: {item?.supervisor_department}</li><li>Учёная степень: {item?.supervisor_degree}</li></ul>}]}/></div>
          <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.qualification}</p>
          <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
          {check_key_card(key_list, item?.id, item?.reference)}
          <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tags)}</p>
          <div className='flex mb-2 place-self-center'><Button color="primary" variant='outlined' onClick={() => modalConfig(item?.id, item?.theme)} ><span>Получить полную версию ВКР</span></Button></div>
        </Card>
        
      </>
    )
  };
  
  const paramsShow = (params, filter_number, key_list) => {
    if ((params.length > 0))
    {
      if ((params.length > 1) && (filter_number!=1)) {
        return(
        <List>
          <div className='grid grid-cols-2 gap-2'>
            {params.slice(0, filter_number).map(item => {
                return(
                  <div key = {item?.id} className='w-150 text-left text-wrap'>
                    {CardVKR(item, key_list)}
                  </div>)
              })}
          </div> 
        </List>)
      }
      else {
        return(
          <List>
            <div className='place-items-center'>
              {params.slice(0, filter_number).map((item) => <div key = {item?.id} className='w-150 text-left text-wrap'>
                {CardVKR(item, key_list)}
              </div>)}
            </div> 
          </List>
        )
      }
    }};

  const CardList = (params, filter_number, list_key, isLoading) => {
      try {
        if (isLoading) {
          return (<div className='flex'>
            <p className='text-[#242424] mx-2'>Загрузка</p><Spin size='large'/>
          </div>)
          }
        else {
          if ((!filter_number) || (filter_number > params.length)) {
            filter_number = params.length
          }
          else if (filter_number < 1) {
            filter_number = Math.round(params.length*filter_number)
          }
          return (
            <>
              <div className="self-center m-2 text-center place-items-center">
                <p className='mb-2'>Количество результатов: {filter_number}</p>
                <div className='w-100 self-center bg-slate-500 rounded-lg place-items-center'>            
                  <Collapse className='w-100' items={[{label: <span className='text-white'>Фильтр</span>, children: <div className='flex text-center justify-center w-90'><span className='mb-2 place-self-center'>Показать {<InputNumber min={0} max={params.length} onChange={handleChangeFilter_top}/>} {util.onChange_filter(filter_number)}</span></div>}]}/>
                </div>
              </div>
              {paramsShow(params, filter_number, list_key)}
            </>
            )
      }}
      catch (err) {
        return (
          <p id='noData' className='text-center text-xl'>Извините, нет доступных данных </p>
        )
      }
  };
  
  const main = () => {
      return (
        <div className='flex flex-col place-items-center my-2'>
          <div className='w-200 bg-slate-500 p-6 m-2 rounded-md text-wrap'>
            <h2 className='merriweather'>Репозиторий ВКР</h2>
            <div className='place-items-center'>  
            <div className='w-180'>
              <Form
                {...util.layout}
                form={form}
                layout='vertical'
                name="get_data"
                onSubmitCapture={handleSubmit}
                autoComplete='off'
              >
                <Form.Item name="theme">
                  <div className='flex justify-around w-140'>
                    <div className='w-120'>
                      <Select
                        showSearch
                        mode="multiple"
                        placeholder="Тема ВКР"
                        onChange={SelectChange_theme}
                        options={getThemes}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                      />
                    </div>
                    <div>
                      <Popover content={<li className='w-90 ml-4 text-wrap'>В поле "Тема ВКР" можно выбрать несколько тем</li>}>
                        <InfoCircleOutlined style={{fontSize: '28px', color: 'white'}}/>
                      </Popover>
                    </div>
                  </div>             
                </Form.Item>
                <Form.Item name="qualification">
                  <div className='flex justify-around w-140'>
                    <div className='w-120'>
                      <Select
                        placeholder="Выберите квалификацию"
                        onChange = {SelectChange_qualification}
                        allowClear
                      >
                        <Option value="Бакалавриат">Бакалавриат</Option>
                        <Option value="Магистратура">Магистратура</Option>
                      </Select>
                    </div>
                    <div>
                      <Popover content={<li className='w-120 ml-4 text-wrap'>В поле "Квалификация" можно выбрать одно из значений: Бакалавриат или Магистратура</li>}>
                        <InfoCircleOutlined style={{fontSize: '28px', color: 'white'}}/>
                      </Popover>
                    </div>
                  </div>   
                </Form.Item>
                <Form.Item name="supervisor_">
                   <div className='flex justify-around w-140'>
                    <div className='w-120'>
                      <Select
                        showSearch
                        mode="multiple"
                        placeholder="Выберите научного руководителя"
                        onChange={SelectChange_supervisor}
                        options={getSupervisors}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                      />
                    </div>
                    <div>
                      <Popover content={<li className='w-120 ml-4 text-wrap'>В поле "Научный руководитель" можно выбрать несколько научных руководителей</li>}>
                        <InfoCircleOutlined style={{fontSize: '28px', color: 'white'}}/>
                      </Popover>
                    </div>
                  </div>     
                </Form.Item>
                <Form.Item name="tags_">
                  <div className='flex justify-around w-140'>
                    <div className='w-120'>
                      <Select
                        showSearch
                        mode='tags'
                        placeholder="Выберите или введите тэг"
                        onChange={SelectChange_tags}
                        options={getTags}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                      />
                    </div>
                    <div className='self-center'>
                      <Popover content={<ul id="note-list" className='list-inside w-210 '>
                            <li className='my-2'>Тэги помогают с поиском ВКР, если отсутствуют ключевые слова; можно выбрать несколько тэгов</li>
                            <li className='my-2'>ВАЖНО! Если тэг отсутствует в предложенном списке, то его можно ввести в поле "Тэги". В данном случае будут показаны работы с наиболее близкими по тематике тэгами</li>
                          </ul>}>
                        <InfoCircleOutlined style={{fontSize: '28px', color: 'white'}}/>
                      </Popover>
                    </div>
                  </div>   
                </Form.Item>
                <Form.Item {...util.tailLayout}>
                  <div className='flex justify-center'>
                    <Space>
                      <Button onClick = {() =>{
                        getPasskeyInitial(backend_url, visitor, headers)
                        fetchData(dataGQW, backend_url)
                        setFilter(0)
                      }} type="primary" htmlType="submit">
                        Поиск
                      </Button>
                      <Button htmlType="button" onClick={onReset}>
                        Сбросить
                      </Button>
                    </Space>
                  </div>
                </Form.Item>
              </Form>
            </div>
            </div>
          </div>
          {CardList(gqwForm, filter, passkey, isLoading)}
      </div>
      ) 
  };

  return (
    <>
      {contextHolder_notification}
      {contextHolder_modal}
      {main()}
    </>
  )
};


export {App_main};