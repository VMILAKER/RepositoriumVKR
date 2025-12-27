import { useEffect, useState } from 'react'
import axios from 'axios'
import { Button, Form, Input, Select, Space,List, Card, Spin, Collapse,Modal, InputNumber, message } from 'antd';
import * as util from './Utilities.jsx';


const initialFormState = {
  theme_:  '',
  supervisor_: '',
  qualification_: '',
  tags_:''
};

const byVisitorId = {
  visitor_id: '',
  password: '',
  gqw_id: ''
}
const checkKey = {
  visitor_id: '',
  password: '',
  gqw_id: '',
  theme: ''
};


function App_main() {
  const { Option } = Select;
  const [dataGQW, setGQW] = useState(initialFormState);
  const [gqwForm, setGqwData] = useState([]);
  const [filter, setFilter] = useState(0);
  const [isLoading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const [getSupervisors, setSupervisors] = useState([])
  const [getReferences, setReferences] = useState([])
  const [getDepartments, setDepartments] = useState([])
  const [getDegrees, setDegrees] = useState([])
  const [getThemes, setThemes] = useState([])
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [visitor, setVisitor] = useState(checkKey);
  const [passkey, setPasskey] = useState([])


  const url = "http://10.6.41.116:8001/repositorium"

  const layout = {
    labelCol: { span: 8 },
    wrapperCol: { span: 16 },
    };

    const tailLayout = {
    wrapperCol: { offset: 6, span: 12 },
    };

  
  const get_visitor_id = async() => {
     const fpPromise = import('https://openfpcdn.io/fingerprintjs/v5')
      .then(FingerprintJS => FingerprintJS.load())

    await fpPromise.then(fp => fp.get())
      .then(result => {
        const visitorId = result.visitorId   
        setVisitor({...visitor, visitor_id: (result.visitorId).toString()})
        byVisitorId['visitor_id'] = visitorId
       console.log(byVisitorId['visitor_id'])
      }
    )
  };
  
  function reducedHash() {
    let length=8
    let charset='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    let password_new = ''
    
    for (let i=0; i < length; i++) {
      password_new +=charset.charAt(Math.floor(Math.random() * (charset.length)))
    }

    console.log(password_new)
    visitor['password'] = password_new
  };
  

  const fetchPrior = async(url_) => {
    try {
      let getOptions = [];
      await axios.get(`${url_}/preloaded_data`).then(r => {
        getOptions = r.data
        if (getOptions.length > 0) {
          setThemes(getOptions[0])
          setReferences(getOptions[1])
          setDepartments(getOptions[2])
          setSupervisors(getOptions[3])
          setDegrees(getOptions[4])
          
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
        console.log('response', r.data)
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
  
  const uploadPasskey = async(url_) => { 
    try {
      reducedHash()
      alert(`Ваш пароль для '${visitor['theme']}': ${visitor['password']}`)
      console.log(visitor)
      await axios.post(`${url_}/add_passkey`, visitor)
      let resp = getPasskeyInitial(url_, visitor)
      paramsShow(gqwForm, gqwForm.length, resp)
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
        console.log(resp)
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
      console.log(param)
       await axios.get(`${url_}/get_gqw_by_passkey?password=${param['password']}&gqw_id=${param['gqw_id']}`, {param} ).then(r => {
        let resp = r.data
        console.log(resp)
        if (!(resp == 'Unvalid key')) {
          axios.post(`${url}/add_passkey`, visitor)

          let resp_init = getPasskeyInitial(url_, param)
          alert('Успешно добавлена полная версия')
          paramsShow(gqwForm, gqwForm.length, resp_init)          
        }
        if (resp === 'Unvalid key') {
          alert('Unvalid key')
        }
        setIsModalOpen(false)
       })
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };

  const showModal = (item, name) => {
    visitor['gqw_id'] = item
    byVisitorId['gqw_id'] = item
    setVisitor({...visitor, theme:name})
    setIsModalOpen(true);
  };

  const handleOk = () => {
    getPasskey(url, byVisitorId)
    setIsModalOpen(false);
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

  const SelectChange_qualification = (event) => {
    setGQW({...dataGQW, qualification_: event})
  };

  const SelectChange_supervisor = (event) => {
    let superv_list = []
    superv_list.push(event)
    setGQW({...dataGQW, supervisor_: superv_list.join(',')})
  };

  const handleChangeFilter_top = (event) => {
    setFilter(event*1)
  };

  const handleChangeFilter_percent = (event) => {
    setFilter(event/100)
  };
  
  const inputPasskey = (event) => {
    byVisitorId['password'] = event.target.value
  };

  const onReset = () => {
    form.resetFields();
    setGQW(initialFormState)
    setFilter(0)
  };
  
  const saveLink = (str) => {
    localStorage.setItem('sharedValue', str)
  };
  
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
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: </span><a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(`full_pdf/${link}`)} target="_blank" >Полный текст</a>/ <a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(link)} target="_blank" >Аннотация</a></p>
        )}
      else {
        return (
          <p className='my-2'><span className='font-bold'>Ссылка на ВКР: <a className='text-justify' href={`http://10.6.41.116:5174/pdf_viewer`} onClick={() => saveLink(link)} target="_blank" >Аннотация</a></span></p>
          )
        }
    };

    return( 
      <>
        <Card component='span' styles={{'title':{'textWrap': "wrap"}}} title={item?.theme}>
          <div className='flex items-center'><span className='font-bold'>Руководитель: </span><Collapse className='w-130' size='small' items={[{label:item?.supervisor_gqw.name, children: <ul><li>Место работы: {item?.supervisor_gqw.department_gqw.department}</li><li>Учёная степень: {item?.supervisor_gqw.degree_gqw.degree}</li></ul>}]}/></div>
          <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.type_of_qualification.qualification}</p>
          <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
          {check_key_card(key_list, item?.id, item?.reference)}
          <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tag_gqw)}</p>
          <div className='mb-2 place-self-center'><Button color="primary" variant='outlined' onClick={() => showModal(item?.id, item?.theme)} ><span>Получить полную версию ВКР</span></Button></div>
        </Card>
        <Modal
          title="Получить полную версию ВКР"
          closable={{ 'aria-label': 'Custom Close Button' }}
          open={isModalOpen}
          onOk={handleOk}
          okText='Проверить ключ'
          cancelText='Отмена'
          onCancel={handleCancel}
        >
    
          <Input className='my-2' name="passkey" placeholder='Введите ключ доступа' onChange={inputPasskey} allowClear/>  
          <Button color="primary" variant='solid' onClick={() => uploadPasskey(url)}>Получить ключ доступа к полному тексту ВКР</Button>
        </Modal>
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
            <p className='text-[#242424] mx-2'>Loading</p><Spin size='large'/>
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
                <div className='w-100 self-center bg-slate-500 rounded-lg self-center'>            
                  <Collapse size='small' items={[{label: 'Фильтр', children: <div className='flex text-center'><span className='mb-2'>Показать {filter_number} работ: {<InputNumber min={0} max={params.length} onChange={handleChangeFilter_top}/>} </span><span>Процент от всех записей, %: {<InputNumber min={1} max={100} onChange={handleChangeFilter_percent}/>} </span></div>}]}/>
                </div>
              </div>
              {paramsShow(params, filter_number, list_key)}
            </>
            )
      }}
      catch (err) {
        return (
          <p id='noData' className='text-center text-xl'>Sorry, there is no data available </p>
        )
      }
  };
  
  const main = () => {
      return (
        <div className='flex flex-col place-items-center my-2'>
          {contextHolder}
          <div className='flex w-290 bg-slate-500 p-6 m-2 rounded-md text-wrap'>
            <div className='w-180'>
              <Form
                {...layout}
                form={form}
                layout='vertical'
                name="get_data"
                onSubmitCapture={handleSubmit}
                autoComplete='off'
              >
                <Form.Item name="theme" label="Тема">
                  <Input name="theme_" placeholder='Тема ВКР' onChange = {handleChange} allowClear/>
                </Form.Item>
                <Form.Item name="qualification" label="Квалификация">
                  <Select
                    placeholder="Выберите квалификацию"
                    onChange = {SelectChange_qualification}
                    allowClear
                  >
                    <Option value="Бакалавриат">Бакалавриат</Option>
                    <Option value="Магистратура">Магистратура</Option>
                  </Select>
                </Form.Item>
                <Form.Item name="supervisor_" label="Научный руководитель">
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
                </Form.Item>
                <Form.Item name="tags_" label="Тэги">
                  <Input name="tags_" placeholder='Поисковые тэги ВКР' onChange = {handleChange} allowClear/>
                </Form.Item>
                <Form.Item {...tailLayout}>
                  <Space>
                    <Button onClick = {() =>{
                      getPasskeyInitial(url, byVisitorId)
                      fetchData(dataGQW, url)
                      console.log("here",dataGQW)
                      setFilter(0)
                    }} type="primary" htmlType="submit">
                      Поиск
                    </Button>
                    <Button htmlType="button" onClick={onReset}>
                      Сбросить
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
            {util.noteGet()}
          </div>
          {CardList(gqwForm, filter, passkey, isLoading)}
      </div>
      ) 
  };

  return (
    <>
      {main()}
    </>
  )
};


export {App_main};