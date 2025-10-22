import { useEffect, useState } from 'react'
import axios from 'axios'
import { Button, Form, Input, Select, Space,List, Card, Spin, Switch, Collapse, Upload, Checkbox, InputNumber, message} from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import {CardVKR} from './components/Card.jsx'
import * as util from './components/Utilities.jsx';

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
  const [selectedFile, setSelectedFile] = useState(null);
  const [filter, setFilter] = useState(0);
  const [isLoading, setLoading] = useState(false);
  const [isUploading, setUploading] = useState(false);
  const [isChecked, setChecked] = useState(false);
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const [getSupervisors, setSupervisors] = useState([])
  const [getReferences, setReferences] = useState([])
  const [getDepartments, setDepartments] = useState([])
  const [getDegrees, setDegrees] = useState([])
  const [getThemes, setThemes] = useState([])


  const url = "http://10.6.41.116:8001/repositorium"
  
  // Error $ success message
  const messageSystem = (type_message, params, key) => {
    messageApi.open({
      key,
      type: type_message,
      content: params,
      duration: 4,
    });
  };



  // Check if the is .pdf
  const props = {
    maxCount: 1,
    multiple: false,
    beforeUpload: info => {
      const isPdf = info.type === 'application/pdf'
      if (!isPdf) {
        messageSystem('error', `${info.name} is not a pdf file`, 'notPdf')
        return isPdf || Upload.LIST_IGNORE
      }
      else {
        if (!(getReferences.includes(info.name, 0))) {
          setSelectedFile(info)
          setDataUpload({...dataUpload, reference: info.name})
          return false
        }
        else {
          messageSystem('error', `${info.name} already exists`, 'pdfExists')
        }
      }
    }
  };
  
  // Fetching supervisors and references
  const fetchAllData = async(url_) => {
    let bin = [];
    let bin_departments = [];
    let bin_degree = [];
    let getOptions = [];
    
    let options_superv = [];
    let appointed_reference = [];
    let departments = [];
    let degrees = [];
    let themes = [];
    try {
      await axios.get(url_).then(r => {
        getOptions = r.data
        if (getOptions.length > 0) {
          for (let i=0; i<getOptions.length; i++) {
            if (!(bin.includes(getOptions[i]?.supervisor_gqw.name, 0))) {
              options_superv.push({label: getOptions[i]?.supervisor_gqw.name, value: getOptions[i]?.supervisor_gqw.name})
              bin.push(getOptions[i]?.supervisor_gqw.name)
            }
            if (!(themes.includes(getOptions[i]?.theme, 0))) {
              themes.push(getOptions[i]?.theme)
            }
            if (!(appointed_reference.includes(getOptions[i]?.reference, 0))) {
              appointed_reference.push(getOptions[i]?.reference)
            }
            if (!(bin_departments.includes(getOptions[i]?.supervisor_gqw.department_gqw.department, 0))) {
              departments.push({label: getOptions[i]?.supervisor_gqw.department_gqw.department, value: getOptions[i]?.supervisor_gqw.department_gqw.department})
              bin_departments.push(getOptions[i]?.supervisor_gqw.department_gqw.department)
            }
            if (!(bin_degree.includes(getOptions[i]?.supervisor_gqw.degree_gqw.degree, 0))) {
              degrees.push({label: getOptions[i]?.supervisor_gqw.degree_gqw.degree, value: getOptions[i]?.supervisor_gqw.degree_gqw.degree})
              bin_degree.push(getOptions[i]?.supervisor_gqw.degree_gqw.degree)
            }
        }}
      })
      setSupervisors(options_superv)
      setReferences(appointed_reference)
      setDepartments(departments)
      setDegrees(degrees)
      setThemes(themes)
      // return [options_superv, appointed_reference, departments, degrees, themes]
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
  };
  
  useEffect(() => {
    fetchAllData(url)
  }, [url])
  
  // Fetch data by certain dynamic parameters
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

  // Upload data
  const uploadData = async(dataUpload, url_) => {
    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      let empty_fields =0 
      for (let i in dataUpload) {
        if (!(dataUpload[i])) {
          empty_fields++
        }
      }
      if (empty_fields == 0) {
        if (!(getThemes.includes(dataUpload?.theme, 0))) {
          messageSystem('loading', 'Download in progress', 'loadingData')
          await axios.post(`${url_}/create_file`, formData)
          await axios.post(`${url_}/post`, dataUpload)
          messageSystem('success', `Data is downloaded!`, 'uploadSuccess')
          fetchAllData(url)
        }
        else {
          message.destroy('loadingData')
          messageSystem('error', `${dataUpload?.theme} already exists!`, 'themeExists')
        }
      }
      else {
        alert("Can't be transferred because fields is empty!")
      }
    }
    catch(err) {
      console.error('Error', err)
      alert(`Something wrong: ${err}`)
    }
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

  const SelectChange_qualification_upload = (event) => {
    setDataUpload({...dataUpload, type_of_qualification: event})
  };
  const SelectChange_supervisor_upload = (event) => {
      setDataUpload({...dataUpload, supervisor: event})
  };

  const SelectChange_department_upload = (event) => {
    setDataUpload({...dataUpload, department:event[0]})
  };

  const SelectChange_degree_upload = (event) => {
    setDataUpload({...dataUpload, degree:event[0]})
  };

  const SelectChange_supervisor = (event) => {
    let superv_list = []
    superv_list.push(event)
    setGQW({...dataGQW, supervisor_: superv_list.join(',')})
  };

  const handleChange_upload = (event) => {
    setDataUpload({...dataUpload, [event.target.name]: event.target.value})
  };
  
  const handleChangeFilter_top = (event) => {
    setFilter(event*1)
  }

  const handleChangeFilter_percent = (event) => {
    setFilter(event/100)
  }

  const onReset = () => {
    form.resetFields();
    setGQW(initialFormState)
    setFilter(0)
  };
  
  const onResetUpload = () => {
    form.resetFields()
    setDataUpload(formUpload)
  }

  function onChange_checkboxSupervisor() {
    if (!isChecked) {
      return (
        <Select name='supervisor'
          showSearch
          placeholder="Выберите научного руководителя"
          onChange={SelectChange_supervisor_upload}
          options={getSupervisors}
          optionFilterProp='label'
          filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
          allowClear
        />
      )
    }
    else {
      return (
      <div className='ml-6'>
        <Input className='my-1' name="supervisor" placeholder='Фамилия И.О. научного руководителя' onChange = {handleChange_upload} allowClear/>
        <Select name='department'
          showSearch
          mode='tags'
          placeholder="Выберите или введите место работы"
          onChange={SelectChange_department_upload}
          options={getDepartments}
          optionFilterProp='label'
          filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
          allowClear
        />
        <div className="my-1">
          <Select name='degree' 
            showSearch
            mode='tags'
            placeholder="Выберите или введите учёную степень"
            onChange={SelectChange_degree_upload}
            options={getDegrees}
            optionFilterProp='label'
            filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
            allowClear
          />
        </div>
      </div>)
    }
  }
  const paramsShow = (params, filter_number) => {
    if (params.length > 0)
    {
      if ((params.length > 1) && (filter_number!=1)) {
        return(
        <List>
          <div className='grid grid-cols-2 gap-2'>
            {params.slice(0, filter_number).map((item) => <div key = {item.id} className='w-150 text-left text-wrap'>
              {CardVKR(item)}
            </div>)}
          </div> 
        </List>
        )
      }
      else {
        return(
          <List>
            <div className='place-items-center'>
              {params.slice(0, filter_number).map((item) => <div key = {item.id} className='w-150 text-left text-wrap'>
                {CardVKR(item)}
              </div>)}
            </div> 
          </List>
        )
      }
    }};
  const CardList = (params, filter_number, isLoading) => {
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
                  <Collapse size='small' items={[{label: 'Фильтр', children: <div className='flex text-center'><span className='mb-2'>Топ-{filter_number} записей: {<InputNumber min={0} max={params.length} onChange={handleChangeFilter_top}/>} </span><span>Процент от всех записей, %: {<InputNumber min={1} max={100} onChange={handleChangeFilter_percent}/>} </span></div>}]}/>
                </div>
              </div>
              {paramsShow(params, filter_number)}
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
    if (!isUploading) {
      return (
        <div className='flex flex-col place-items-center my-2'>
          <Switch className='w-36 self-center' unCheckedChildren="Поиск ВКР" onChange={() => {setUploading(!isUploading)}}/>
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
                      fetchData(dataGQW, url)
                      console.log("here",dataGQW)
                      setFilter(0)
                    }} type="primary" htmlType="submit">
                      Submit
                    </Button>
                    <Button htmlType="button" onClick={onReset}>
                      Reset
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
            {util.noteGet()}
          </div>
          {CardList(gqwForm, filter, isLoading)}
      </div>
      ) 
    }
    else {
      return(
        <div className="flex flex-col pt-2 place-items-center bg-amber-400">
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
                    name='quallification'
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
                  {onChange_checkboxSupervisor()}
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
                      uploadData(dataUpload, url)
                      console.log("transfer",dataUpload)
                    }
                      } type="primary" htmlType="submit">
                      Submit
                    </Button>
                    <Button htmlType="button" onClick={onResetUpload}>
                      Reset
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
           {util.noteUpload()}
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