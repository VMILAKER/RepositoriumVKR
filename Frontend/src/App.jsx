import { useEffect, useState } from 'react'
import axios from 'axios'
import { Button, Form, Input, Select, Space,List, Card, Spin, Switch, Collapse, Upload, Checkbox, Pagination, InputNumber, message} from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const { Option } = Select;


const initialFormState = {
  theme_:  '',
  supervisor_: '',
  qualification_: '',
  tags_:''
};

const formUpload = {
  theme: '',
  supervisor: '', 
  type_of_qualification: '',
  abstract: '',
  reference: '',
  tags: ''


};

const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};

const tailLayout = {
  wrapperCol: { offset: 6, span: 12 },
};

function App_main() {
  const [dataGQW, setGQW] = useState(initialFormState);
  const [gqwForm, setGqwData] = useState([]);
  const [dataUpload, setDataUpload] = useState(formUpload);
  const [getOptions, setOptions] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [getNumber, setNumber] = useState(0)
  const [isLoading, setLoading] = useState(false);
  const [isUploading, setUploading] = useState(false);
  const [isChecked, setChecked] = useState(false);
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();

  // Error $ success message
  const messageSystem = (type_message, params) => {
    messageApi.open({
      type: type_message,
      content: params,
      duration: 4,
    });
  };

  // Building of lists with all supervisors and references
  let options_superv = [];
  let appointed_reference = []
  const bin =[]
  for (let i=0; i<getOptions.length; i++) {
    if (!(bin.includes(getOptions[i]?.supervisor_gqw.name, 0))) {
      options_superv.push({label: getOptions[i]?.supervisor_gqw.name, value:getOptions[i]?.supervisor_gqw.name})
      bin.push(getOptions[i]?.supervisor_gqw.name)
    }
    if (!(bin.includes(getOptions[i]?.reference, 0))) {
      appointed_reference.push(getOptions[i]?.reference)
      bin.push(getOptions[i]?.reference)
    }
  }
  options_superv.sort(function (a, b) {
    if (a.value < b.value) {
      return -1;
    }
    if (a.name > b.name) {
      return 1;
    }
    return 0;
  });

  // Check if the is .pdf
  const props = {
    maxCount: 1,
    multiple: false,
    beforeUpload: info => {
      const isPdf = info.type === 'application/pdf'
      if (!isPdf) {
        messageSystem('error', `${info.name} is not a pdf file`)
        return isPdf || Upload.LIST_IGNORE
      }
      else {
        if (!(appointed_reference.includes(info.name, 0))) {
          console.log(appointed_reference)
          setSelectedFile(info)
          setDataUpload({...dataUpload, reference: info.name})
          return false
        }
        else {
          messageSystem('error', `${info.name} already exists`)
        }
      }
    }
  }
  
  // Fetching supervisors and references
  const fetchAllData = async() => {
    let url = `http://127.0.0.1:8000/repositorium/`
    try {
      await axios.get(url).then(r => {
        setOptions(r.data)
        })}
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };
  
  useEffect(() => {
    fetchAllData()    
  }, [])
  
  // Fetch data by certain dynamic parameters
  const fetchData = async({dataGQW}) => {   
    setLoading(true) 
    setNumber(0)
    const params = {}
    let url = `http://127.0.0.1:8000/repositorium/`

    for (let i in dataGQW) {
      if (dataGQW[i]) {
        params[i] = dataGQW[i]
      }
    }

    try {
      await axios.get(url, {params} ).then(r => {
        console.log('response', r.data)
        const response = r.data
        setGqwData(response)
        setLoading(false)
      })
      }
    catch(err) {
    console.error('Error', err)
    alert(`Something wrong: ${err}`)
    }
  };

  // Upload data
  const uploadData = async({dataUpload}) => {
    let url = 'http://127.0.0.1:8000/repositorium/post'
    
    const formData = new FormData()
    formData.append('file', selectedFile)
    console.log(formData)

    try {
      let gol =0 
      for (let i in dataUpload) {
        if (!(dataUpload[i])) {
          gol++
        }
      }
      if (gol == 0) {
        await axios.post(`http://127.0.0.1:8000/repositorium/create_file`, formData)
        await axios.post(url, dataUpload)
        messageSystem('success', `Data is downloaded!`)
      }
      else {
        alert("Can't be transferred because fields is empty!")
      }
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  }
  // const {theme, qualification, resp} = dataGQW; That's wrong
  
  
  const handleSubmit = async event => {
    event.preventDefault()
  };
  const handleChange = (event) => {
    setGQW({...dataGQW, [event.target.name]: event.target.value})
  };

  const SelectChange_qualification = (event) => {
    setGQW({...dataGQW, qualification_: event})
  };

  const SelectChange_qualification_upload = (event) => {
    setDataUpload({...dataUpload, type_of_qualification: event})
  };

  const SelectChange_supervisor = (event) => {
    let superv_list = []
    superv_list.push(event)
    setGQW({...dataGQW, supervisor_: superv_list.join(',')})
  };

  const SelectChange_supervisor_upload = (event) => {
      setDataUpload({...dataUpload, supervisor: event})
  };
  
  const handleChange_upload = (event) => {
    setDataUpload({...dataUpload, [event.target.name]: event.target.value})
  };
  
  const handleChangeFilter_top = (event) => {
      setNumber(event)
  }

  const handleChangeFilter_percent = (event) => {
      setNumber(event/100)
  }

  const onReset = () => {
    form.resetFields();
  };
  
  const tag_array = (param) => {
    let final_tag = []
    for (let i in param) {
      final_tag.push(param[i].tag_name)
    }
    return final_tag.join(', ')
  };

  const onChange_checkbox = () => {
    if (!isChecked) {
      return (
        <Select name='qualification'
        placeholder="Выберите научного руководителя"
        onChange={SelectChange_supervisor_upload}
        options={options_superv}
        allowClear
        />
      )
    }
    else {
      return (
      <div className='ml-6'>
        <Input className='my-1' name="supervisor" placeholder='Фамилия И.О. научного руководителя' onChange = {handleChange_upload} allowClear/>
        <Input className='my-1' name="department" placeholder='Место работы' onChange = {handleChange_upload} allowClear/>
        <Input className='my-1' name="degree" placeholder='Учёная степень научного руководителя' onChange = {handleChange_upload} allowClear/>
      </div>)
    }
  }


  const outputCardList = (params, filter_number) => {
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
          else if (filter_number <= 1) {
            filter_number = Math.round(params.length*filter_number)
          }
          return (
            <div className="place-items-center m-2 text-center">
                <p className='mb-2'>Количество результатов: {filter_number}</p>
              <div className='w-100 bg-slate-500 rounded-lg'>            
                <Collapse size='small' items={[{label: 'Фильтр', children: <ul className='text-left'><li className='mb-2'>Топ-{filter_number} записей: {<InputNumber name='top' min={1} max={params.length} onChange={handleChangeFilter_top}/>}</li><li>Процент от всех записей, %: {<InputNumber name='percent' min={1} max={100} onChange={handleChangeFilter_percent}/>} </li></ul>}]}/>
              </div>
              <List>
                  {params.length >0 && params.slice(0, filter_number).map((item) => <div key = {item.id} className='w-170 my-4 text-left text-wrap'>
                    <Card component='span' title={`ВКР_${item?.type_of_qualification}`}>
                    <p className='my-2'><span className='font-bold'>Тема: </span>{item?.theme}</p>
                    <div className='flex items-center my-2'><span className='font-bold'>Руководитель: </span><Collapse className='w-100' size='small' items={[{label:item?.supervisor_gqw.name, children: <ul><li>Место работы: {item?.supervisor_gqw.department}</li><li>Учёная степень: {item?.supervisor_gqw.degree}</li></ul>}]}/></div>
                    <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.type_of_qualification}</p>
                    <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
                    <p className='my-2'><span className='font-bold'>Ссылка на аннотацию: </span><a className='text-justify' href={`http://localhost:5173/pdf_docs/${item?.reference}`} target="_blank" >{item?.reference}</a></p>
                    <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tag_gqw)}</p>
                  </Card>
                  </div>)}
              </List>
            </div>
            )
      }}
      catch (err) {
        return (
          <p id='noData' className='text-center text-xl'>Sorry, there is no data available </p>
        )
      }
  };
  
  const main = () => {
    if (!isUploading) {
      return (
        <div className="place-items-center">
          <Switch className='w-36' unCheckedChildren="Поиск ВКР" onChange={() => {setUploading(!isUploading)}}/>
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
                  mode="multiple"
                  placeholder="Выберите научного руководителя"
                  onChange={SelectChange_supervisor}
                  options={options_superv}
                  allowClear
                  />
                </Form.Item>
                <Form.Item name="tags_" label="Тэги">
                  <Input name="tags_" placeholder='Поисковые тэги ВКР' onChange = {handleChange} allowClear/>
                </Form.Item>
                <Form.Item {...tailLayout}>
                  <Space>
                    <Button onClick = {() =>{
                      fetchData({dataGQW})
                      console.log("here",dataGQW)
                    }
                      } type="primary" htmlType="submit">
                      Submit
                    </Button>
                    <Button htmlType="button" onClick={onReset}>
                      Reset
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
            <div className="w-120 text-justify text-white">
              <h2 className='text-center font-semibold text-lg'>Памятка</h2>
              <ul id="note-list" className='list-disc'>
                <li className='my-2'>Поиск по теме ВКР осуществляется на основе ключевого слова; можно вводить значения в следующем формате: Ключевое слово1, Ключевое слово2</li>
                <li className='my-2'>В поле "Квалификация" можно выбрать одно из значений: Бакалавриат или Магистратура</li>
                <li className='my-2'>В поле "Научный руководитель" можно выбрать несколько научных руководителей</li>
                <li className='my-2'>Тэги помогают с поиском ВКР, если отсутствуют ключевые слова (например, при вводе тэга "Shipment" программа выведет "Адаптивная модель грузоперевозок"); можно вводить значения в следующем формате: тэг1, тэг2</li>
              </ul>
            </div>
          </div>
          {outputCardList(gqwForm, getNumber)}
      </div>
      ) 
    }
    else {
      return(
        <div className="place-items-center bg-amber-500 h-full">
          <Switch className='w-36' checkedChildren="Добавление ВКР" onChange={() => {setUploading(!isUploading)}}/>
          {contextHolder}
          <div className='flex w-290 bg-slate-500 p-6 m-2 rounded-md text-wrap'>
            <div className='w-180'>
              <Form
                {...layout}
                form={form}
                layout='vertical'
                name="upload_data"
                onSubmitCapture={handleSubmit}
                autoComplete='off'
              >
                <Form.Item name="theme_upload" label="Тема">
                  <Input name="theme" placeholder='Тема ВКР' onChange = {handleChange_upload} allowClear/>
                </Form.Item>
                <Form.Item name="type_of_qualification" label="Квалификация">
                  <Select
                    placeholder="Выберите квалификацию"
                    onChange = {SelectChange_qualification_upload}
                    allowClear
                  >
                    <Option value="Бакалавриат">Бакалавриат</Option>
                    <Option value="Магистратура">Магистратура</Option>
                    
                  </Select>
                </Form.Item>
                <Form.Item>
                  <Checkbox onChange={() => {setChecked(!isChecked)}}>Руководителя нет в списке</Checkbox>
                  {onChange_checkbox(isChecked)}
                </Form.Item>
                <Form.Item name="abstract" label="Аннотация">
                  <Input name="abstract" placeholder='Введите аннотацию' onChange = {handleChange_upload} allowClear/>
                </Form.Item>
                <Form.Item name='reference' label='Файл аннотации (.pdf)'>
                  <Upload {...props}>
                    <Button icon={<UploadOutlined/>} >Click to upload</Button>
                  </Upload>
                </Form.Item>
                <Form.Item name="tags" label="Тэги">
                  <Input name="tags" placeholder='Поисковые тэги ВКР' onChange = {handleChange_upload} allowClear/>
                </Form.Item>
                <Form.Item {...tailLayout}>
                  <Space>
                    <Button onClick = {() =>{
                      uploadData({dataUpload})
                      console.log("transfer",dataUpload)
                    }
                      } type="primary" htmlType="submit">
                      Submit
                    </Button>
                    <Button htmlType="button" onClick={onReset}>
                      Reset
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
            <div className="w-130 text-justify text-white">
                <h2 className='text-center font-semibold text-lg'>Памятка</h2>
                <ul id="note-list" className='list-disc'>
                  <li className='my-2'>Тема ВКР должна начинаться с заглавной буквы</li>
                  <li className='my-2'>В поле "Квалификация" можно выбрать одно из значений: Бакалавриат или Магистратура</li>
                  <li className='my-2'>В поле "Научный руководитель" можно выбрать только одного руководителя; если руководителя нет в списке, то необходимо поставить 'галочку' в окне 'Руководителя нет в списке' и заполнить его данные: Фамилию И.О., место работы и учёную степень</li>
                  <li className='my-2'>Аннотация должна совпадать с текстом аннотации ВКР</li>
                  <li className='my-2'>Принимаются файлы только в формате .pdf; название файла должно быть на английском языке без ФИО автора ВКР (например, тема Адаптивная модель грузоперевозок будет иметь название 'Adaptive_model.pdf')</li>
                  <li className='my-2'>Тэги вводятся на английском языке исходя из тематики ВКР (например, тема Адаптивная модель грузоперевозок может иметь тэги 'Cargo, Shipment')</li>
                </ul>
              </div>
          </div>
        </div>
      )
    }
  };

  return (
    <>
      {main()}
    </>
  )
};


export default App_main