import { useEffect, useLayoutEffect, useState, useRef } from 'react'
import axios from 'axios'
import { Button, Form, Input, Select, Space,List, Card, Spin, Collapse,Modal, InputNumber, Popover, notification } from 'antd';
import {InfoCircleOutlined} from '@ant-design/icons'
import * as util from './Utilities.jsx';


const initialFormState = {
  theme_:  '',
  supervisor_: '',
  qualification_: '',
  tags_:''
};

const uploadKey = {
  visitor_id: '',
  gqw_id: '',
  theme: ''
}
const checkKey = {
  visitor_id: '',
  password: '',
  gqw_id: '',
  theme: ''
};

const stylesShared = {
  label:{
      color:'#ffffff',
  }
};


function App_main() {
  const { Option } = Select;
  const refContainer= useRef(null);
  const [dataGQW, setGQW] = useState(initialFormState);
  const [gqwForm, setGqwData] = useState([]);
  const [filter, setFilter] = useState(0);
  const [isLoading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [api, contextHolder_notification] = notification.useNotification();
  const [getThemes, setThemes] = useState([]);
  const [getSupervisors, setSupervisors] = useState([]);
  const [getTags, setTags] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [getVisitorUpload, uploadVisitor] = useState(uploadKey);
  const [visitor, setVisitor] = useState(checkKey);
  const [passkey, setPasskey] = useState([]);
  const [modal, contextHolder_modal] = Modal.useModal();
  const [widthB, setWidth] = useState(0);

  const modalConfig = (item, name) => {
    visitor['gqw_id'] = item
    visitor['theme'] =name
    getVisitorUpload['gqw_id'] = item
    getVisitorUpload['theme'] = name
    
    modal.confirm({
      title: 'Получить полную версию ВКР',
      closable: {'aria-label': 'Custom Close Button' },
      width: 450,
      state: {blur: false},
      okText: 'Проверить ключ',
      onOk() {getPasskey(url, visitor)},
      cancelText: "Отмена",
      onCancel() {handleCancel},
      content: (
        <div>
          <Input ref={refContainer} className='my-2' name="passkey" placeholder='Введите ключ доступа' onChange={inputPasskey} allowClear/>  
          <Button style={{width: 370}} color="primary" variant='solid' onClick={() => uploadPasskey(url, getVisitorUpload)}>Получить ключ доступа к полному тексту ВКР</Button>
        </div>
        )
      
    })
  }
  const url = "http://url/repository"

  const layout = {
    labelCol: { span: 8 },
    wrapperCol: { span: 16 },
    };

    const tailLayout = {
    wrapperCol: { offset: 6, span: 12 },
    };

  const openNotificationWithIcon = (type, param) => {
    api[type]({
      description:
        param,
    });
  };
  
  const get_visitor_id = async() => {
     const fpPromise = import('https://openfpcdn.io/fingerprintjs/v5')
      .then(FingerprintJS => FingerprintJS.load())

    await fpPromise.then(fp => fp.get())
      .then(result => {
        setVisitor({...visitor, visitor_id: (result.visitorId).toString()})
        uploadVisitor({...getVisitorUpload, visitor_id: (result.visitorId).toString()})

      }
    )
  };
  

  const fetchPrior = async(url_) => {
    try {
      let getOptions = [];
      await axios.get(`${url_}/preloaded_data`).then(r => {
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
    fetchPrior(url)
    get_visitor_id()
  }, [url]);
  
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
      await axios.get(url_, {params} ).then(r => {
        // console.log('response', r.data)
        let response = r.data
        if ((response.length >= 2) && (!(response == 'Nothing to say')) && (!(response == "No findings by tag's query"))) {
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
  
  const uploadPasskey = async(url_, param) => { 
    try {
      // console.log(param)
      await axios.post(`${url_}/add_passkey`, param).then(r => {
        let responce = r.data
        openNotificationWithIcon('info', `Ваш пароль для '${param['theme']}': ${responce}`)
        let resp = getPasskeyInitial(url_, param)
        paramsShow(gqwForm, gqwForm.length, resp)
      })
      setIsModalOpen(false);
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const getPasskeyInitial = async(url_, param) => {
    try {
       await axios.get(`${url_}/get_gqw_by_passkey?visitor_id=${param['visitor_id']}`, {param} ).then(r => {
        let resp = r.data
        // console.log(resp)
        if (!(resp == 'No data'))
          setPasskey(resp)
       })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const getPasskey = async(url_, param) => {
    try {
      // console.log(param)
       await axios.get(`${url_}/get_gqw_by_passkey?password=${param['password']}&gqw_id=${param['gqw_id']}`, {param} ).then(r => {
        let resp = r.data
        // console.log(resp)
        if (!(resp == 'Unvalid key')) {
          axios.post(`${url_}/add_passkey`, param).then(r=> {
            let resp_init = getPasskeyInitial(url_, param)
            openNotificationWithIcon('success', 'Успешно добавлена полная версия')
            paramsShow(gqwForm, gqwForm.length, resp_init)
          })
          setIsModalOpen(false);        
        }
        else {
          openNotificationWithIcon('error', 'Неправильный ключ')
          setIsModalOpen(false); 
        }
       })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const handleCancel = (target) => {
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
    setGQW({...dataGQW, theme_: theme_list.join(',')})
  };

  const SelectChange_qualification = (event) => {
    setGQW({...dataGQW, qualification_: event})
  };

  const SelectChange_supervisor = (event) => {
    let superv_list = []
    superv_list.push(event)
    setGQW({...dataGQW, supervisor_: superv_list.join(',')})
  };


  const SelectChange_tags = (event) => {
    let tag_list = []
    tag_list.push(event)
    setGQW({...dataGQW, tags_:tag_list.join(',')})
  };

  const handleChangeFilter_top = (event) => {
    setFilter(event*1)
  };

  const inputPasskey = (event) => {
    visitor['password'] = event.target.value
  };

  const onReset = () => {
    form.resetFields();
    setGQW(initialFormState)
    setFilter(0)
  };
  
  const saveLink = (str) => {
    localStorage.setItem('sharedValue', str)
  };
  
  const onChange_filter = (num) => {
    let number = num.toString()
    if (number.length >= 2) {
      if ((['0', '5', '6', '7', '8', '9'].includes(number.slice(-1))) || (['11', '12', '13', '14'].includes(number.slice(-2)))) {
        return 'работ'
      }
      else if ((['2', '3', '4'].includes(number.slice(-1))) && !(['11', '12', '13', '14'].includes(number.slice(-2)))) {
        return 'работы'
      }
      else if ((['1'].includes(number.slice(-1))) && !(['11'].includes(number.slice(-2)))) {
        return 'работу'
      }
    }
    else if ((number.length === 1))
      if (['1'].includes(number)) {
        return 'работу'
      }
      else if (['2', '3', '4'].includes(number)) {
        return 'работы'
      }
      else if (['0', '5', '6', '7', '8', '9'].includes(number)) {
        return 'работ'
      }
  }
  function CardVKR(item, key_list) {

    const tag_array = (param) => {
      let final_tag = []
      for (let i in param) {
        final_tag.push(param[i].tag_name)
      }
      return final_tag.join(', ')
    };

    const check_key_card = (key_list, param, link) => { 
      if (Array.from(key_list).find(o => o.id == param)) {
        return (
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: </span><a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(`full_pdf/${link}`)} target="_blank" >Полный текст</a>/ <a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(`compressed/${link}`)} target="_blank" >Аннотация</a></p>
        )}
      else {
        return (
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: <a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(`compressed/${link}`)} target="_blank" >Аннотация</a></span></p>
          )
        }
    };

    return( 
      <>
        <Card component='span' styles={{'title':{'textWrap': "wrap"}}} title={item?.theme}>
          <div className='flex items-center'><span className='font-bold mr-2'>Руководитель: </span><Collapse className='w-130' size='small' items={[{label:item?.supervisor_gqw.name, children: <ul><li>Место работы: {item?.supervisor_gqw.department_gqw.department}</li><li>Учёная степень: {item?.supervisor_gqw.degree_gqw.degree}</li></ul>}]}/></div>
          <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.type_of_qualification.qualification}</p>
          <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
          {check_key_card(key_list, item?.id, item?.reference)}
          <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tag_gqw)}</p>
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
                  <Collapse className='w-100' items={[{label: <span className='text-white'>Фильтр</span>, children: <div className='flex text-center justify-center w-90'><span className='mb-2 place-self-center'>Показать {<InputNumber min={0} max={params.length} onChange={handleChangeFilter_top}/>} {onChange_filter(filter_number)}</span></div>}]}/>
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
                {...layout}
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
                <Form.Item {...tailLayout}>
                  <div className='flex justify-center'>
                    <Space>
                      <Button onClick = {() =>{
                        getPasskeyInitial(url, visitor)
                        fetchData(dataGQW, url)
                        // console.log("here",dataGQW)
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